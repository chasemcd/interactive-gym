from __future__ import annotations

import atexit
import logging
import os
import secrets
import threading
import uuid
import msgpack
import pandas as pd
import os
import flatten_dict
import json

import flask
import flask_socketio
import redis

from interactive_gym.utils.typing import SubjectID, SceneID
from interactive_gym.scenes import gym_scene
from interactive_gym.server import game_manager as gm

from interactive_gym.configurations import remote_config
from interactive_gym.server import utils
from interactive_gym.scenes import stager
from interactive_gym.server import game_manager as gm
from interactive_gym.scenes import unity_scene

try:
    import redis
except Exception as e:
    print(
        f"Unable to import redis, got the following Exception. If you want to use the message queue, you must install redis. {e}"
    )


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
    subject_id = SESSION_ID_TO_SUBJECT_ID.get(session_id, None)
    return subject_id


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
except Exception as e:
    print(f"An unexpected error occurred when trying to connect to redis: {e}")
    message_queue = None

socketio = flask_socketio.SocketIO(
    app,
    cors_allowed_origins="*",
    logger=app.config["DEBUG"],
    message_queue=message_queue,
    # engineio_logger=False,
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

    return flask.render_template(
        "index.html",
        async_mode=socketio.async_mode,
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
    logger.info(f"Registered session ID {sid} with subject {subject_id}")
    participant_stager = STAGERS[subject_id]
    participant_stager.start(socketio, room=sid)

    participant_stager.current_scene.export_metadata(subject_id)


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
    participant_stager.advance(socketio, room=flask.request.sid)

    # If the current scene is a GymScene, we'll instantiate a
    # corresponding GameManager to handle game logic, connections,
    # and waiting rooms.
    current_scene = participant_stager.get_current_scene()
    logger.info(
        f"Advanced to scene: {current_scene.scene_id}. Metadata export: {current_scene.should_export_metadata}"
    )
    if isinstance(current_scene, gym_scene.GymScene):
        logger.info(
            f"Instantiating game manager for scene {current_scene.scene_id}"
        )
        game_manager = gm.GameManager(
            scene=current_scene, experiment_config=CONFIG, sio=socketio
        )
        GAME_MANAGERS[current_scene.scene_id] = game_manager

    if current_scene.should_export_metadata:
        current_scene.export_metadata(subject_id)


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

        if game_manager is None:
            logger.error(
                f"Subject {subject_id} tried to join a game but no game manager was found for scene {current_scene.scene_id}."
            )
            return

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
            room=flask.request.sid,
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
    # return
    # sess_id = flask.request.sid
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    subject_id = flask.session.get("subject_id")
    # print(subject_id, sess_id, STAGERS)

    # # TODO(chase): figure out why we're getting a different session ID here...
    participant_stager = STAGERS.get(subject_id, None)
    if participant_stager is None:
        logger.error(
            f"Pressed keys requested for {subject_id} but they don't have a Stager."
        )
        return

    current_scene = participant_stager.current_scene
    game_manager = GAME_MANAGERS.get(current_scene.scene_id, None)
    # game = game_manager.get_subject_game(subject_id)

    client_reported_server_session_id = data.get("server_session_id")
    # print(client_reported_server_session_id, "send_pressed_keys")
    # print(sess_id, subject_id, "send_pressed_keys")
    # if not is_valid_session(
    #     client_reported_server_session_id, subject_id, "send_pressed_keys"
    # ):
    #     return

    pressed_keys = data["pressed_keys"]

    game_manager.process_pressed_keys(
        subject_id=subject_id, pressed_keys=pressed_keys
    )


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


@socketio.on("unityEpisodeEnd")
def on_unity_episode_end(data):

    # TODO(chase): remove this
    import random

    model = random.choice(
        [
            "4fs-16od-082992f-0.03to0.01-sp",
            "4fs-16od-13c7f7b-0.05to0.01-sp-00",
            "4fs-16od-13c7f7b-0.05to0.01-sp-03",
        ]
    )
    frame_skip = random.choice([4, 8, 16, 32])
    obs_delay = random.choice([16, 32])
    inference_cadence = 4
    socketio.emit(
        "updateBotSettings",
        {
            "modelPath": model,
            "frameSkip": frame_skip,
            "inferenceCadence": inference_cadence,
            "observationDelay": obs_delay,
            "softmaxTemperature": 1.0,
        },
    )
    print(data)
    ###
    subject_id = get_subject_id_from_session_id(flask.request.sid)
    participant_stager = STAGERS.get(subject_id, None)
    current_scene = participant_stager.current_scene

    if not isinstance(current_scene, unity_scene.UnityScene):
        return

    current_scene.on_unity_episode_end(
        data,
        sio=socketio,
        room=flask.request.sid,
    )

    # (Potentially) save the data
    scene_id = current_scene.scene_id
    cur_episode = current_scene.episodes_completed
    wrapped_data = {}
    wrapped_data["scene_id"] = f"{scene_id}_{cur_episode}"
    wrapped_data["data"] = data

    # TODO(chase): Make sure the globals are propagated here
    # so we don't have to fill it.
    wrapped_data["interactiveGymGlobals"] = {}

    data_emission(wrapped_data)


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


@socketio.on("static_scene_data_emission")
def data_emission(data):
    """Save the static scene data to a csv file."""

    if not CONFIG.save_experiment_data:
        return

    subject_id = get_subject_id_from_session_id(flask.request.sid)
    # Save to a csv in data/{scene_id}/{subject_id}.csv
    # Save the static scene data to a csv file.
    scene_id = data.get("scene_id")
    if not scene_id:
        logger.error("Scene ID is required to save data.")
        return

    # Create a directory for the CSV files if it doesn't exist
    os.makedirs(f"data/{scene_id}/", exist_ok=True)

    # Generate a unique filename
    filename = f"data/{scene_id}/{subject_id}.csv"
    globals_filename = f"data/{scene_id}/{subject_id}_globals.json"

    # Save as CSV
    logger.info(f"Saving {filename}")

    # convert to a list so we can save it as a csv
    for k, v in data["data"].items():
        data["data"][k] = [v]

    df = pd.DataFrame(data["data"])

    df["timestamp"] = pd.to_datetime("now")

    if CONFIG.save_experiment_data:
        df.to_csv(filename, index=False)

        with open(globals_filename, "w") as f:
            json.dump(data["interactiveGymGlobals"], f)


@socketio.on("emit_remote_game_data")
def receive_remote_game_data(data):

    if not CONFIG.save_experiment_data:
        return

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

    # Convert to DataFrame
    df = pd.DataFrame(padded_data)

    # Create a directory for the CSV files if it doesn't exist
    os.makedirs(f"data/{data['scene_id']}/", exist_ok=True)

    # Generate a unique filename
    filename = f"data/{data['scene_id']}/{subject_id}.csv"
    globals_filename = f"data/{data['scene_id']}/{subject_id}_globals.json"

    # Save as CSV
    logger.info(f"Saving {filename}")

    if CONFIG.save_experiment_data:
        df.to_csv(filename, index=False)
        with open(globals_filename, "w") as f:
            json.dump(data["interactiveGymGlobals"], f)

    # Also get the current scene for this participant and save the metadata
    # TODO(chase): this has issues where the data may not be received before the
    # scene is advanced, which results in this getting the metadata for the _next_
    # scene.

    # participant_stager = STAGERS.get(subject_id, None)
    # if participant_stager is None:
    #     logger.error(
    #         f"Subject {subject_id} tried to save data but they don't have a Stager."
    #     )
    #     return

    # current_scene = participant_stager.current_scene
    # current_scene_metadata = current_scene.get_complete_scene_metadata()

    # # save the metadata to a json file
    # with open(f"data/{data['scene_id']}/{subject_id}_metadata.json", "w") as f:
    #     json.dump(current_scene_metadata, f)


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
