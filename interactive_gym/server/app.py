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
import msgpack
import pandas as pd
import os
import flatten_dict
import json

import eventlet
import flask
import flask_socketio
import redis
from eventlet import queue

from interactive_gym.utils.typing import SubjectID, GameID, SceneID
from interactive_gym.scenes import gym_scene
from interactive_gym.server import game_manager as gm


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


def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(
        formatter
    )  # Setting the formatter for the console handler as well

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(ch)
    logger.propagate = False

    return logger


logger = setup_logger(__name__, "./iglog.log", level=logging.DEBUG)

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
    print("session_id", session_id, SESSION_ID_TO_SUBJECT_ID)
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
    global STAGERS, SESSION_ID_TO_SUBJECT_ID, SUBJECTS

    if subject_id in PROCESSED_SUBJECT_NAMES:
        return (
            "Error: You have already completed the experiment with this ID!",
            404,
        )

    SUBJECTS[subject_id] = threading.Lock()

    participant_stager = GENERIC_STAGER.build_instance()
    STAGERS[subject_id] = participant_stager
    participant_stager.start(socketio)

    participant_stager = STAGERS[subject_id]
    start_scene = participant_stager.current_scene

    return flask.render_template(
        "index.html",
        async_mode=socketio.async_mode,
        scene_header=start_scene.scene_header,
        scene_body=start_scene.scene_body,
        subject_id=subject_id,
    )


@socketio.on("register_subject")
def register_subject(data):
    global SESSION_ID_TO_SUBJECT_ID
    """Ties the subject name in the URL to the flask request sid"""
    subject_id = data["subject_id"]
    sid = flask.request.sid
    flask.session["subject_id"] = subject_id
    SESSION_ID_TO_SUBJECT_ID[sid] = subject_id
    print("registering subject")
    logger.info(f"Registered session ID {sid} with subject {subject_id}")


# @socketio.on("connect")
# def on_connect():
#     global SESSION_ID_TO_SUBJECT_ID

#     subject_id = get_subject_id_from_session_id(flask.request.sid)

#     if subject_id in SUBJECTS:
#         return

#     SUBJECTS[subject_id] = threading.Lock()

#     # TODO(chase): reenable session checkings
#     # Send the current server session ID to the client
#     # flask_socketio.emit(
#     #     "server_session_id",
#     #     {"server_session_id": SERVER_SESSION_ID},
#     #     room=subject_id,
#     # )


@socketio.on("advance_scene")
def advance_scene(data):
    global GAME_MANAGERS
    """Advance the scene to the next one."""
    subject_id = get_subject_id_from_session_id(flask.request.sid)

    participant_stager: stager.Stager | None = STAGERS.get(subject_id, None)
    if participant_stager is None:
        raise ValueError(f"No stager found for subject {subject_id}")

    participant_stager.advance(socketio)

    # If the current scene is a GymScene, we'll instantiate a
    # corresponding GameManager to handle game logic, connections,
    # and waiting rooms.
    current_scene = participant_stager.get_current_scene()
    if isinstance(current_scene, gym_scene.GymScene):
        game_manager = gm.GameManager(
            scene=current_scene, experiment_config=CONFIG, sio=socketio
        )
        GAME_MANAGERS[current_scene.scene_id] = game_manager


@socketio.on("join_game")
def join_game(data):

    subject_id = get_subject_id_from_session_id(flask.request.sid)
    client_session_id = data.get("server_session_id")

    # Validate session
    # if not is_valid_session(client_session_id, subject_id, "join_game"):
    #     return

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


def is_valid_session(
    client_session_id: str, subject_id: SubjectID, context: str
) -> bool:
    valid_session = client_session_id == SERVER_SESSION_ID

    if not valid_session:
        logger.warning(
            f"Invalid session for {subject_id} in {context}. Got {client_session_id} but expected {SERVER_SESSION_ID}"
        )
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=subject_id,
        )

    return valid_session


@socketio.on("leave_game")
def leave_game(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    logger.info(f"Participant {subject_id} leaving game.")

    # Validate session
    client_reported_session_id = data.get("session_id")
    # if not is_valid_session(
    #     client_reported_session_id, subject_id, "leave_game"
    # ):
    #     return

    with SUBJECTS[subject_id]:
        # If the participant doesn't have a Stager, something is wrong at this point.
        participant_stager = STAGERS.get(subject_id, None)
        if participant_stager is None:
            logger.error(
                f"Subject {subject_id} tried to leave a game but they don't have a stager."
            )
            return

        # Get the current scene and game manager to determine where to send the participant
        current_scene = participant_stager.current_scene
        game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)

        game_manager.leave_game(subject_id=subject_id)
        PROCESSED_SUBJECT_NAMES.append(subject_id)


# @socketio.on("disconnect")
# def on_disconnect():
#     global SUBJECTS
#     subject_id = get_subject_id_from_session_id(flask.request.sid)

#     participant_stager = STAGERS.get(subject_id, None)
#     if participant_stager is None:
#         logger.error(
#             f"Subject {subject_id} tried to join a game but they don't have a Stager."
#         )
#         return

#     current_scene = participant_stager.current_scene
#     game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)

#     # Get the current game for the participant, if any.
#     game = game_manager.get_subject_game(subject_id)

#     if game is None:
#         logger.info(
#             f"Subject {subject_id} disconnected with no coresponding game."
#         )
#     else:
#         logger.info(
#             f"Subject {subject_id} disconnected, Game ID: {game.game_id}.",
#         )

#     with SUBJECTS[subject_id]:
#         game_manager.leave_game(subject_id=subject_id)

#     del SUBJECTS[subject_id]
#     if subject_id in SUBJECTS:
#         logger.warning(
#             f"Tried to remove {subject_id} but it's still in SUBJECTS."
#         )


@socketio.on("send_pressed_keys")
def send_pressed_keys(data):
    """
    Translate pressed keys into game action and add them to the pending_actions queue.
    """
    return
    # # sess_id = flask.request.sid
    # subject_id = get_subject_id_from_session_id(flask.request.sid)
    # # subject_id = flask.session.get("subject_id")
    # # print(subject_id, sess_id, STAGERS)

    # # TODO(chase): figure out why we're getting a different session ID here...
    # participant_stager = STAGERS.get(subject_id, None)
    # if participant_stager is None:
    #     logger.error(
    #         f"Pressed keys requested for {subject_id} but they don't have a Stager."
    #     )
    #     return

    # current_scene = participant_stager.current_scene
    # game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)
    # # game = game_manager.get_subject_game(subject_id)

    # client_reported_server_session_id = data.get("server_session_id")
    # if not is_valid_session(
    #     client_reported_server_session_id, subject_id, "send_pressed_keys"
    # ):
    #     return

    # pressed_keys = data["pressed_keys"]

    # game_manager.process_pressed_keys(
    #     subject_id=subject_id, pressed_keys=pressed_keys
    # )


@socketio.on("reset_complete")
def handle_reset_complete(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    client_session_id = data.get("session_id")

    # if not is_valid_session(client_session_id, subject_id, "reset_complete"):
    #     return

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


@socketio.on("data_emission")
def data_emission(data):
    print("Data emission", data)


@socketio.on("emit_remote_game_data")
def receive_remote_game_data(data):
    subject_id = get_subject_id_from_session_id(flask.request.sid)

    # Decode the msgpack data
    decoded_data = msgpack.unpackb(data["data"])

    # Flatten any nested dictionaries
    flattened_data = flatten_dict.flatten(decoded_data, reducer="dot")

    # Find the maximum length among all values
    max_length = max(
        len(value) if isinstance(value, list) else 1
        for value in flattened_data.values()
    )

    # Pad shorter lists with None and convert non-list values to lists
    padded_data = {}
    for key, value in flattened_data.items():
        if not isinstance(value, list):
            padded_data[key] = [value] + [None] * (max_length - 1)
        else:
            padded_data[key] = value + [None] * (max_length - len(value))

    for key, value in padded_data.items():
        print(key, type(value), len(value))

    # Convert to DataFrame
    df = pd.DataFrame(padded_data)
    print(df.head())

    # Create a directory for the CSV files if it doesn't exist
    os.makedirs(f"data/{data['scene_id']}/", exist_ok=True)

    # Generate a unique filename
    filename = f"data/{data['scene_id']}/{subject_id}.csv"

    # Save as CSV
    print("Saving to", filename)
    df.to_csv(filename, index=False)


# def periodic_log() -> None:
#     """Log information at specified 30s interval"""
#     while True:
#         logger.info(
#             f"{time.ctime(time.time())}, there are {len(ACTIVE_GAMES)} active games, {len(WAITING_GAMES)} waiting games, {len(GAMES)} total games, and {len(SUBJECTS)} participants."
#         )
#         eventlet.sleep(30)


def run(config):
    global app, CONFIG, logger, GENERIC_STAGER
    CONFIG = config
    GENERIC_STAGER = config.stager

    atexit.register(on_exit)
    socketio.run(
        app,
        log_output=app.config["DEBUG"],
        port=CONFIG.port,
        host=CONFIG.host,
    )
