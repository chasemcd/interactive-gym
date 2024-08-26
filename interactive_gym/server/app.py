from __future__ import annotations

import atexit
import base64
import itertools
import logging
import os
import random
import secrets
import threading
import time
import uuid

import eventlet
import flask
import flask_socketio
import redis
from eventlet import queue

from interactive_gym.utils.typing import SubjectID, GameID, SceneID


try:
    import cv2
except ImportError:
    cv2 = None
    print(
        "cv2 not installed. This is required if you're not "
        "defining a rendering function and want to (inefficiently) "
        "have the canvas display whatever is returned from `env.render('rgb_array')`."
    )

from interactive_gym.configurations import (
    configuration_constants,
    remote_config,
)
from interactive_gym.server import remote_game, utils
from interactive_gym.scenes import stager
from interactive_gym.server import game_manager as gm


CONFIG = remote_config.RemoteConfig()


# Generic stager is the "base" Stager that we'll build for each
# participant that connects to the server. This is the base instance
# that defines the generic experiment flow.
GENERIC_STAGER: stager.Stager = None  # Instantiate on run()

# Each participant has their own instance of the Stager to manage
# their progression through the experiment.
STAGERS: dict[SubjectID, stager.Stager] = utils.ThreadSafeDict()

# Data structure to save subjects by their socket id
SUBJECTS = utils.ThreadSafeDict()

# Game managers handle all the game logic, connection, and waiting room for a given scene
GAME_MANAGERS: dict[SceneID, gm.GameManager] = utils.ThreadSafeDict()

# Mapping of users to locks associated with the ID. Enforces user-level serialization
USER_LOCKS = utils.ThreadSafeDict()


# Session ID to participant ID map
SESSION_ID_TO_SUBJECT_ID = utils.ThreadSafeDict()


def get_subject_id_from_session_id(session_id: str) -> SubjectID:
    return SESSION_ID_TO_SUBJECT_ID.get(session_id, None)


# List of subject names that have entered a game (collected on end_game)
PROCESSED_SUBJECT_NAMES = []

# Number of games allowed
MAX_CONCURRENT_SESSIONS: int | None = 1

# Generate a unique identifier for the server session
SERVER_SESSION_ID = secrets.token_urlsafe(16)


#######################
# Flask Configuration #
#######################

app = flask.Flask(__name__, template_folder=os.path.join("static", "templates"))
app.config["SECRET_KEY"] = "secret!"

app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"

# check if redis is available to use for message queue
redis_host = "127.0.0.1"
try:
    redis.Redis(redis_host, socket_connect_timeout=1).ping()
    message_queue = f"redis://{redis_host}:6379/0"
except redis.exceptions.ConnectionError:
    print("Redis is not available for message queue. Proceeding without it...")
    message_queue = None

socketio = flask_socketio.SocketIO(
    app,
    cors_allowed_origins="*",
    # logger=app.config["DEBUG"],
    message_queue=message_queue,
)


#######################
# Flask Configuration #
#######################


@app.route("/")
def index(*args):
    """If no subject ID provided, generate a UUID and re-route them."""
    subject_id = str(uuid.uuid4())
    return flask.redirect(flask.url_for("user_index", subject_id=subject_id))


@app.route("/<subject_id>")
def user_index(subject_id):

    if subject_id in PROCESSED_SUBJECT_NAMES:
        return (
            "Error: You have already completed the experiment with this ID!",
            404,
        )

    STAGERS[subject_id] = GENERIC_STAGER.build_instance()
    STAGERS[subject_id].start()

    instructions_html = ""
    if CONFIG.instructions_html_file is not None:
        try:
            with open(CONFIG.instructions_html_file, encoding="utf-8") as f:
                instructions_html = f.read()
        except FileNotFoundError:
            instructions_html = f"<p> Unable to load instructions file {CONFIG.instructions_html_file}.</p>"

    return flask.render_template(
        "index.html",
        async_mode=socketio.async_mode,
        welcome_header_text=CONFIG.welcome_header_text,
        welcome_text=CONFIG.welcome_text,
        instructions_html=instructions_html,
        game_header_text=CONFIG.game_header_text,
        game_page_text=CONFIG.game_page_text,
        final_page_header_text=CONFIG.final_page_header_text,
        final_page_text=CONFIG.final_page_text,
        subject_id=subject_id,
    )


@socketio.on("register_subject_id")
def register_subject_id(data):
    """Ties the subject name in the URL to the flask request sid"""
    subject_id = data["subject_id"]
    sid = flask.request.sid
    flask.session["subject_id"] = subject_id
    SESSION_ID_TO_SUBJECT_ID[sid] = subject_id
    logger.info(f"Registered seesion ID {sid} with subject {subject_id}")


@socketio.on("connect")
def on_connect():
    subject_id = flask.request.sid

    if subject_id in SUBJECTS:
        return

    SUBJECTS[subject_id] = threading.Lock()

    # Send the current server session ID to the client
    flask_socketio.emit(
        "server_session_id",
        {"server_session_id": SERVER_SESSION_ID},
        room=subject_id,
    )


@socketio.on("advance_scene")
def advance_scene():
    """Advance the scene to the next one."""
    subject_id = get_subject_id_from_session_id(flask.request.sid)

    participant_stager: stager.Stager | None = STAGERS.get(subject_id, None)
    if participant_stager is None:
        raise ValueError(f"No stager found for subject {subject_id}")

    participant_stager.advance()


@socketio.on("join_game")
def join_game(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    client_session_id = data.get("server_session_id")

    # Validate session
    if not is_valid_session(client_session_id):
        logger.warning(
            f"Invalid session for {subject_id}. Got {client_session_id} but expected {SERVER_SESSION_ID}"
        )
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=subject_id,
        )
        return

    with SUBJECTS[subject_id]:

        # If the participant doesn't have a Stager, something is wrong at this point.
        participant_stager = STAGERS.get(subject_id, None)
        if participant_stager is None:
            logger.error(
                f"Subject {subject_id} tried to join a game but they don't have a stager."
            )
            return

        # Get the current scene and game manager to determine where to send the participant
        current_scene = participant_stager.current_scene
        game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)

        # Check if the participant is already in a game in this scene, they should not be.
        if game_manager.subject_in_game(subject_id):
            logger.error(
                f"Subject {subject_id} in a game in scene {current_scene.scene_id} but attempted to join another."
            )
            return

        game = game_manager.add_subject_to_game(subject_id)
        logger.info(
            f"Successfully added subject {subject_id} to game {game.game_id}."
        )


@socketio.on("request_pyodide_initialization")
def pyodide_initialization(data):
    """If we're using Pyodide, emit the initialization event.

    TODO(chase): This should allow Pyodide to persist across scenes,
    so we want to iterate through _all_ the scenes and check for Pyodide usage
    and the packages to install.
    """
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    participant_stager = STAGERS.get(subject_id, None)
    current_scene = participant_stager.current_scene

    if CONFIG.run_through_pyodide:
        socketio.emit(
            "initialize_pyodide_remote_game",
            {"config": current_scene.to_dict(serializable=True)},
        )
        return


def is_valid_session(client_session_id):
    return client_session_id == SERVER_SESSION_ID


@socketio.on("leave_game")
def leave_game(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    logger.info(f"Participant {subject_id} leaving game.")

    # Validate session
    client_reported_session_id = data.get("session_id")
    if not is_valid_session(client_reported_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please refresh the page."},
            room=subject_id,
        )
        return

    with SUBJECTS[subject_id]:
        # If the participant doesn't have a Stager, something is wrong at this point.
        participant_stager = STAGERS.get(subject_id, None)
        if participant_stager is None:
            logger.error(
                f"Subject {subject_id} tried to join a game but they don't have a stager."
            )
            return

        # Get the current scene and game manager to determine where to send the participant
        current_scene = participant_stager.current_scene
        game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)

        game_manager.leave_game(subject_id=subject_id)
        PROCESSED_SUBJECT_NAMES.append(subject_id)


@socketio.on("disconnect")
def on_disconnect():
    global SUBJECTS
    subject_id = get_subject_id_from_session_id(flask.request.sid)

    participant_stager = STAGERS.get(subject_id, None)
    if participant_stager is None:
        logger.error(
            f"Subject {subject_id} tried to join a game but they don't have a Stager."
        )
        return

    current_scene = participant_stager.current_scene
    game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)

    # Get the current game for the participant, if any.
    game = game_manager.get_subject_game(subject_id)

    if game is None:
        logger.info(
            f"Subject {subject_id} disconnected with no coresponding game."
        )
    else:
        logger.info(
            f"Subject {subject_id} disconnected, Game ID: {game.game_id}.",
        )

    with SUBJECTS[subject_id]:
        game_manager.leave_game(subject_id=subject_id)

    del SUBJECTS[subject_id]
    if subject_id in SUBJECTS:
        logger.warning(
            f"Tried to remove {subject_id} but it's still in SUBJECTS."
        )


@socketio.on("send_pressed_keys")
def send_pressed_keys(data):
    """
    Translate pressed keys into game action and add them to the pending_actions queue.
    """
    sess_id = flask.request.sid
    subject_id = get_subject_id_from_session_id(sess_id)

    participant_stager = STAGERS.get(subject_id, None)
    if participant_stager is None:
        logger.error(
            f"Subject {subject_id} tried to join a game but they don't have a Stager."
        )
        return

    current_scene = participant_stager.current_scene
    game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)
    game = game_manager.get_subject_game(subject_id)

    client_reported_server_session_id = data.get("server_session_id")
    if not is_valid_session(client_reported_server_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=sess_id,
        )
        return

    pressed_keys = data["pressed_keys"]

    game_manager.process_pressed_keys(
        subject_id=subject_id, pressed_keys=pressed_keys
    )


@socketio.on("reset_complete")
def handle_reset_complete(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    client_session_id = data.get("session_id")

    if not is_valid_session(client_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=subject_id,
        )
        return

    participant_stager = STAGERS.get(subject_id, None)
    game_manager = GAME_MANAGERS.get(
        participant_stager.current_scene.scene_id, None
    )

    game_manager.trigger_reset(subject_id)


@socketio.on("ping")
def pong(data):
    socketio.emit(
        "pong",
        {
            "max_latency": CONFIG.max_ping,
            "min_ping_measurements": CONFIG.min_ping_measurements,
        },
        room=flask.request.sid,
    )

    # TODO(chase): when data tracking is reimplemented, we'll want to track the ping/focus status here.
    # also track if the user isn't focused on their window.
    # game = _get_existing_game(sid)
    # if game is None:
    #     return

    # document_in_focus = data["document_in_focus"]
    # ping_ms = data["ping_ms"]
    # player_name = SUBJECT_ID_MAP[sid]
    # game.update_ping(
    #     player_identifier=player_name,
    #     hidden_status=document_in_focus,
    #     ping=ping_ms,
    # )


@socketio.on("request_redirect")
def on_request_redirect(data):
    waitroom_timeout = data.get("waitroom_timeout", False)
    if waitroom_timeout:
        redirect_url = CONFIG.waitroom_timeout_redirect_url
    else:
        redirect_url = CONFIG.experiment_end_redirect_url

    if CONFIG.append_subject_id_to_redirect:
        redirect_url += get_subject_id_from_session_id(flask.request.sid)

    socketio.emit(
        "redirect",
        {
            "redirect_url": redirect_url,
            "redirect_timeout": CONFIG.redirect_timeout,
        },
        room=flask.request.sid,
    )


def on_exit():
    # Force-terminate all games on server termination
    for game_manager in GAME_MANAGERS.values():
        game_manager.tear_down()

    for game_manager in GAME_MANAGERS.values():
        game_manager.tear_down()


# def periodic_log() -> None:
#     """Log information at specified 30s interval"""
#     while True:
#         logger.info(
#             f"{time.ctime(time.time())}, there are {len(ACTIVE_GAMES)} active games, {len(WAITING_GAMES)} waiting games, {len(GAMES)} total games, and {len(SUBJECTS)} participants."
#         )
#         eventlet.sleep(30)


def run(config):
    global app, CONFIG, logger
    CONFIG = config
    GENERIC_STAGER = config.stager

    atexit.register(on_exit)
    socketio.run(
        app,
        log_output=app.config["DEBUG"],
        port=CONFIG.port,
        host=CONFIG.host,
    )
