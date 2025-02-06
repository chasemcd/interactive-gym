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

CONFIG = remote_config.RemoteConfig()


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


# TODO(chase): logfile should be able to be updated when the CONFIG is updated
logger = None  # setup_logger(__name__, CONFIG.logfile)


# Data structure to save subjects by their socket id
SUBJECTS = utils.ThreadSafeDict()

# Data structure to save subjects games in memory OBJECTS by their socket id
GAMES = utils.ThreadSafeDict()

# Games that are currently being played
ACTIVE_GAMES = utils.ThreadSafeSet()

# Queue of games IDs that are waiting for additional players to join.
WAITING_GAMES = []
WAITROOM_TIMEOUTS = utils.ThreadSafeDict()

# Mapping of users to locks associated with the ID. Enforces user-level serialization
USERS = utils.ThreadSafeDict()

# Map ids to the URL ids
SUBJECT_ID_MAP = utils.ThreadSafeDict()

# List of subject names that have entered a game (collected on end_game)
PROCESSED_SUBJECT_NAMES = []

# Mapping of user id's to the current game (room) they are in
USER_ROOMS = utils.ThreadSafeDict()

# Bitmap that indicates whether ID is currently in use. Game with ID=i is "freed" by setting FREE_MAP[i] = True
# FREE_MAP = utils.ThreadSafeDict()

# Number of games allowed
MAX_CONCURRENT_GAMES: int | None = 1

# Global queue of available IDs. This is how we sync game creation and keep track of how many games are in memory
FREE_IDS: queue.Queue | None = None  # queue.Queue(maxsize=MAX_CONCURRENT_GAMES)

# holds reset events so we only continue in game loop when triggered
RESET_EVENTS = utils.ThreadSafeDict()

# Generate a unique identifier for the server session
SERVER_SESSION_ID = secrets.token_urlsafe(16)


# Utility to add a new game id to the available games
def add_new_game_id() -> str:
    """Adds a new UUID game ID to FREE_IDS and RESET_EVENTS"""
    game_id = None
    try:
        game_id = str(uuid.uuid4())
        FREE_IDS.put(game_id, block=False)
        RESET_EVENTS[game_id] = utils.ThreadSafeDict()
    except queue.Full:
        logger.warning(
            f"Tried to add a new game id to FREE_IDS, but it's full. (size {FREE_IDS.qsize()})"
        )
        pass

    return game_id


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
    # logger=app.config["DEBUG"],
    message_queue=message_queue,
)


def try_create_game() -> (
    tuple[remote_game.RemoteGame | None, None | RuntimeError | Exception]
):
    try:
        game_id = FREE_IDS.get(block=False)
        game = remote_game.RemoteGame(config=CONFIG, game_id=game_id)
    except queue.Empty:
        err = RuntimeError("Server at maximum capacity.")
        return None, err
    except Exception as e:
        return None, e
    else:
        GAMES[game_id] = game
        # FREE_MAP[game_id] = False
        return game, None


def _create_game() -> None:
    """
    Create a new game and add it to WAITING_GAMES and start the lobby timer.
    If creation fails, we emit the create_game_failed event.
    """
    game, err = try_create_game()
    if game is None:
        logger.warning(
            f"Create game failed for subject ID {flask.request.sid} with error {err.__repr__()}"
        )
        socketio.emit(
            "create_game_failed",
            {"error": err.__repr__()},
            room=flask.request.sid,
        )
        return

    WAITING_GAMES.append(game.game_id)
    WAITROOM_TIMEOUTS[game.game_id] = time.time() + (
        CONFIG.waitroom_timeout / 1000
    )  # convert waitroom timeout to seconds


@socketio.on("join_game")
def join_or_create_game(data):
    subject_id = flask.request.sid
    client_session_id = data.get("session_id")

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
        # already in a game so don't join a new one
        if _get_existing_game(subject_id) is not None:
            logger.warning(
                f"Subject {subject_id} in a game but attempted to join another."
            )
            return

        game = _create_or_join_game()
        if game is None:  # there was an error that is now displayed
            return

        with game.lock:
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} joining room {game.game_id}"
            )
            flask_socketio.join_room(game.game_id)
            USER_ROOMS[subject_id] = game.game_id

            # add unique event to sync resets across players
            RESET_EVENTS[game.game_id][subject_id] = eventlet.event.Event()

            available_human_player_ids = game.get_available_human_player_ids()

            # will be the name entered in the url, e.g., MTurk ID or uuid
            player_name = SUBJECT_ID_MAP[subject_id]
            game.add_player(
                random.choice(available_human_player_ids), player_name
            )

            if CONFIG.game_page_html_fn is not None:
                socketio.emit(
                    "update_game_page_text",
                    {
                        "game_page_text": CONFIG.game_page_html_fn(
                            game, player_name
                        )
                    },
                    room=subject_id,
                )

            # If the game is ready to start, we'll remove it from WAITING_GAMES.
            # This prevents any other player from joining it if, for example,
            # we're in a simulated waiting room before starting the game.
            if game.is_ready_to_start():
                WAITING_GAMES.remove(game.game_id)
                assert game.game_id not in WAITING_GAMES

            # If the game is ready to start and we're simulating a
            # waiting room
            if game.is_ready_to_start() and CONFIG.simulate_waiting_room:

                human_player_display = len(game.human_players)

                if len(game.bot_players) > 0:
                    human_player_display += len(game.bot_players) - 1
                else:
                    human_player_display -= 1

                # Subtract 1 off of the remaining to avoid timing issues
                max_randomized_wait_time = int(
                    WAITROOM_TIMEOUTS[game.game_id] - time.time() - 1
                )
                randomized_wait_time = random.choice(
                    range(*CONFIG.waitroom_time_randomization_interval_s)
                )

                if randomized_wait_time <= 0:
                    start_game(game)
                    return
                elif randomized_wait_time > max_randomized_wait_time:
                    randomized_wait_time = max_randomized_wait_time

                logger.info(
                    f"Sending subject {subject_id} to single player waiting room for {randomized_wait_time} seconds (max was {max_randomized_wait_time})."
                )
                socketio.emit(
                    "single_player_waiting_room",
                    {
                        # Remove one from cur_num to make it look like we need 1 more
                        "cur_num_players": human_player_display,
                        "players_needed": 1,
                        "ms_remaining": CONFIG.waitroom_timeout,
                        "wait_duration_s": randomized_wait_time,
                    },
                    room=subject_id,
                )

            elif game.is_ready_to_start():
                start_game(game)

            # If there is a real waiting room
            else:
                send_participant_to_waiting_room(
                    game=game, subject_id=subject_id
                )


@socketio.on("single_player_waiting_room_end")
def on_single_play_wait_room_end(data):
    subject_id = flask.request.sid

    with SUBJECTS[subject_id]:
        game = _get_existing_game(subject_id)

        if game is None:
            logger.warning(
                f"Subject {subject_id} ended single player waiting room but they aren't associated with a game!"
            )
            # TODO(chase): raise an error
            return

        # We check again just in case a player left during the waiting room timeout
        if game.is_ready_to_start():
            logger.info("Single player waiting room ended and game is ready.")
            start_game(game)
        else:
            # Add the game back to WAITING_GAMES
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} was in simulated waiting room but the game is no longer ready to start. Ending the game for them."
            )
            socketio.emit(
                "single_player_waiting_room_failure",
                {},
                room=game.game_id,
            )


def send_participant_to_waiting_room(
    game: remote_game.RemoteGame, subject_id: str | int
) -> None:
    logger.info(f"{SUBJECT_ID_MAP[subject_id]} entering waiting room.")
    remaining_wait_time = (
        WAITROOM_TIMEOUTS[game.game_id] - time.time()
    ) * 1000  # convert seconds to ms
    socketio.emit(
        "waiting_room",
        {
            "cur_num_players": game.cur_num_human_players(),
            "players_needed": len(game.get_available_human_player_ids()),
            "ms_remaining": remaining_wait_time,
        },
        room=subject_id,
    )


def start_game(game: remote_game.RemoteGame) -> None:
    """Helper function with the logic to begin a game."""
    logger.info(
        f"Game {game.game_id} is starting with subjects: {[sid for sid in game.human_players.values()]}"
    )
    ACTIVE_GAMES.add(game.game_id)

    if CONFIG.run_through_pyodide:
        socketio.emit(
            "start_game_pyodide",
            {"config": CONFIG.to_dict(serializable=True)},
            room=game.game_id,
        )
        return

    socketio.emit(
        "start_game",
        {"config": CONFIG.to_dict(serializable=True)},
        room=game.game_id,
    )

    socketio.start_background_task(run_game, game)


def _get_existing_game(subject_id) -> remote_game.RemoteGame | None:
    """check if there's an existing game for this subject"""
    game = GAMES.get(USER_ROOMS.get(subject_id, None), None)
    return game


def _create_or_join_game() -> remote_game.RemoteGame:
    """
    This function will either
        - get a game that is waiting for players
        - create and return a new game
    """

    # Look for games that are waiting for more players
    game = get_waiting_game()
    if game is not None:
        return game

    # Lastly, we'll make a new game and retrieve that
    _create_game()  # adds to waiting game
    game = get_waiting_game()

    assert game is not None, "Game retrieval failed!"

    return game


def get_waiting_game() -> None | remote_game.RemoteGame:
    if WAITING_GAMES:
        return GAMES.get(WAITING_GAMES[0], None)

    return None


def _cleanup_game(game: remote_game.RemoteGame):
    global WAITING_GAMES, ACTIVE_GAMES, GAMES, RESET_EVENTS

    # Remote all remaining human players from the game
    for player_name in game.human_players.values():
        subject_id = None
        for sid, p_name in SUBJECT_ID_MAP.items():
            if p_name == player_name:
                subject_id = sid
                break

        if player_name is utils.Available:
            continue

        if subject_id is None:
            logger.warning(
                f"Tried to find subject ID for player name {player_name} but it doesn't exist in SUBJECT_ID_MAP"
            )

        logger.info(
            f"In _cleanup_game, removing {player_name} from USER_ROOMS and their reset event from RESET_EVENTS (game id: {game.game_id})"
        )

        remove_participant_from_game(game, subject_id)

    game.tear_down()

    # Close the socketio room
    socketio.close_room(game.game_id)

    # If the game was still in the waiting room, remove it.
    if game.game_id in WAITING_GAMES:
        logger.info(
            f"On _cleanup, {game.game_id} was waiting. Removing from WAITING_GAMES"
        )
        WAITING_GAMES.remove(game.game_id)
        assert game.game_id not in WAITING_GAMES
    else:
        logger.info(f"On _cleanup, {game.game_id} was not waiting.")

    if game.game_id in ACTIVE_GAMES:
        ACTIVE_GAMES.remove(game.game_id)

    old_game_id = game.game_id
    del RESET_EVENTS[old_game_id]
    del GAMES[old_game_id]
    logger.info(f"Successfully cleared out game: {old_game_id}")

    # Add a new game_id to FREE_IDS
    new_game_id = add_new_game_id()

    logger.info(
        f"Successfully added a new game_id to available games: {new_game_id}."
    )


def remove_participant_from_game(
    game: remote_game.RemoteGame, subject_id: int | str
) -> None:
    """Remove a participant from a game and clean up the artifacts"""
    global USER_ROOMS, RESET_EVENTS

    with app.app_context():
        flask_socketio.leave_room(game.game_id)

    del USER_ROOMS[subject_id]
    del RESET_EVENTS[game.game_id][subject_id]
    game.remove_human_player(SUBJECT_ID_MAP[subject_id])


def _leave_game(subject_id) -> bool:
    """Removes the subject with `subject_id` from any current game."""
    game = _get_existing_game(subject_id)

    if game is None:
        logger.info(f"{SUBJECT_ID_MAP[subject_id]} left and game is None.")
        return False

    logger.info(f"{SUBJECT_ID_MAP[subject_id]} leaving game {game.game_id}")

    with game.lock:
        remove_participant_from_game(game, subject_id=subject_id)

        game_was_active = game.game_id in ACTIVE_GAMES and game.status in [
            remote_game.GameStatus.Active,
            remote_game.GameStatus.Reset,
        ]
        game_is_empty = game.cur_num_human_players() == 0

        # If the game was running but there are no other players,
        # we can cleanly end it.
        if game_was_active and game_is_empty:
            exit_status = utils.GameExitStatus.ActiveNoPlayers
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} left game {game.game_id} with exit status {exit_status}. Cleaning up."
            )
            _cleanup_game(game)

        # If the game wasn't active and there are no players,
        # cleanup the traces of the game.
        elif game_is_empty:
            exit_status = utils.GameExitStatus.InactiveNoPlayers
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} left game {game.game_id} with exit status {exit_status}. Cleaning up."
            )
            _cleanup_game(game)

        # if the game was not active and not empty, the remaining players are still in the waiting room.
        elif not game_was_active:
            exit_status = utils.GameExitStatus.InactiveWithOtherPlayers
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} left game {game.game_id} with exit status {exit_status}. Keeping remaining players in the waiting room."
            )

            # If the game isn't already a waiting game, add it back (e.g., participant left in simulated waiting room.)
            if game.game_id not in WAITING_GAMES:
                logger.info(
                    f"Adding {game.game_id} back to WAITING GAMES since a subject left."
                )
                WAITING_GAMES.append(game.game_id)
            # send_participant_to_waiting_room(game, subject_id=game.game_id)
            # remaining_wait_time = (WAITROOM_TIMEOUTS[game.game_id] - time.time()) * 1000
            # # TODO(chase): check if we need this?
            # socketio.emit(
            #     "waiting_room",
            #     {
            #         "cur_num_players": game.cur_num_human_players(),
            #         "players_needed": len(game.get_available_human_player_ids()),
            #         "ms_remaining": remaining_wait_time,  # convert to ms remaining
            #     },
            #     room=game.game_id,
            # )

        # elif game_was_active and game.is_ready_to_start():
        #     raise ValueError("This shouldn't happen without spectators.")
        elif game_was_active and not game_is_empty:
            exit_status = utils.GameExitStatus.ActiveWithOtherPlayers
            logger.info(
                f"Subject {SUBJECT_ID_MAP[subject_id]} left game {game.game_id} with exit status {exit_status}. Cleaning up."
            )

            socketio.emit(
                "end_game",
                (
                    {
                        "message": "You were matched with a partner but your game ended because the other player disconnected."
                    }
                ),
                room=game.game_id,
            )

            _cleanup_game(game)

        else:
            raise NotImplementedError("Something went wrong on exit!")

    return exit_status


@app.route("/")
def index(*args):
    """If no subject ID provided, generate a UUID and re-route them."""
    subject_id = str(uuid.uuid4())
    return flask.redirect(flask.url_for("user_index", subject_id=subject_id))


@app.route("/<subject_id>")
def user_index(subject_id):

    if subject_id in PROCESSED_SUBJECT_NAMES:
        return "Error: You have already played with under this subject ID!", 404

    flask.session["subject_id"] = subject_id

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
    SUBJECT_ID_MAP[sid] = subject_id
    logger.info(f"Registered subject ID {sid} with name {subject_id}")


@socketio.on("request_pyodide_initialization")
def check_pyodide_usage(data):
    """If we're using Pyodide, emit the initialization event."""
    if CONFIG.run_through_pyodide:
        socketio.emit(
            "initialize_pyodide_remote_game",
            {"config": CONFIG.to_dict(serializable=True)},
        )
        return


def is_valid_session(client_session_id):
    return client_session_id == SERVER_SESSION_ID


@socketio.on("connect")
def on_connect():
    subject_id = flask.request.sid

    if subject_id in SUBJECTS:
        return

    SUBJECTS[subject_id] = threading.Lock()

    # Send the current server session ID to the client
    flask_socketio.emit(
        "server_session_id", {"session_id": SERVER_SESSION_ID}, room=subject_id
    )


@socketio.on("leave_game")
def on_leave(data):
    subject_id = flask.request.sid
    client_session_id = data.get("session_id")
    logger.info(f"Participant {SUBJECT_ID_MAP[subject_id]} leaving game.")

    # Validate session
    if not is_valid_session(client_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please refresh the page."},
            room=subject_id,
        )
        return

    with SUBJECTS[subject_id]:
        game = _get_existing_game(subject_id=subject_id)
        if game is not None:
            game_id = game.game_id
        else:
            game_id = None

        game_exit_status = _leave_game(subject_id)
        if game_exit_status in [
            utils.GameExitStatus.ActiveNoPlayers,
            utils.GameExitStatus.ActiveWithOtherPlayers,
        ]:
            if CONFIG.callback is not None:
                CONFIG.callback.on_game_end(game)
            socketio.emit(
                "end_game",
                {},
                room=game_id,
            )

            # track players that have already been in a game
            for human_player_name in game.human_players.values():
                PROCESSED_SUBJECT_NAMES.append(human_player_name)
        else:
            socketio.emit("end_lobby", room=game_id)


@socketio.on("disconnect")
def on_disconnect():
    global SUBJECTS
    subject_id = flask.request.sid
    game = _get_existing_game(subject_id)

    try:
        logger.info(
            f"Subject {SUBJECT_ID_MAP[subject_id]} disconnected, Game ID: {game.game_id if game is not None else 'None'}.",
        )
    except KeyError:
        logger.warning(
            f"Subject {subject_id} disconnected, but they aren't in SUBJECT_ID_MAP."
        )

    if subject_id not in SUBJECTS:
        logger.warning(
            f"Subject {subject_id} disconnected, but they aren't in SUBJECTS."
        )
        return

    logger.info(
        f"Calling _leave_game for {subject_id} ({SUBJECT_ID_MAP[subject_id]}).",
    )
    with SUBJECTS[subject_id]:
        _leave_game(subject_id)

    logger.info(
        f"Removing subject {subject_id} ({SUBJECT_ID_MAP[subject_id]}) from SUBJECTS.",
    )

    del SUBJECTS[subject_id]

    if subject_id in SUBJECTS:
        logger.warning(
            f"Tried to remove {subject_id} ({SUBJECT_ID_MAP[subject_id]}) but it's still in SUBJECTS."
        )


@socketio.on("send_pressed_keys")
def on_action(data):
    """
    Translate pressed keys into game action and add them to the pending_actions queue.
    """
    subject_id = flask.request.sid

    if subject_id not in SUBJECT_ID_MAP:
        return

    game = _get_existing_game(subject_id)

    # Sometimes keys arrive but the game already ended
    if game is None:
        return

    player_name = SUBJECT_ID_MAP[subject_id]
    client_session_id = data.get("session_id")

    # Validate session
    if not is_valid_session(client_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=subject_id,
        )
        return

    pressed_keys = data["pressed_keys"]

    # No keys pressed, queue the default action
    if len(pressed_keys) == 0:
        game.enqueue_action(player_name, CONFIG.default_action)

    elif len(pressed_keys) > 1:
        if not CONFIG.game_has_composite_actions:
            pressed_keys = pressed_keys[:1]
        else:
            pressed_keys = generate_composite_action(pressed_keys)

    if game is None:
        return

    if not any([k in CONFIG.action_mapping for k in pressed_keys]):
        return

    action = None
    for k in pressed_keys:
        if k in CONFIG.action_mapping:
            action = CONFIG.action_mapping[k]
            break

    assert action is not None

    game.enqueue_action(player_name, action)


def generate_composite_action(pressed_keys) -> list[tuple[str]]:

    # TODO(chase): set this in the config so we don't recalculate every time
    max_composite_action_size = max(
        [len(k) for k in CONFIG.action_mapping.keys() if isinstance(k, tuple)]
        + [0]
    )

    if max_composite_action_size > 1:
        composite_actions = [
            action
            for action in CONFIG.action_mapping
            if isinstance(action, tuple)
        ]

        composites = [
            tuple(sorted(action_comp))
            for action_comp in itertools.combinations(
                pressed_keys, max_composite_action_size
            )
        ]
        for composite in composites:
            if composite in composite_actions:
                pressed_keys = [composite]
                break

    return pressed_keys


@socketio.on("reset_complete")
def handle_reset_complete(data):
    subject_id = flask.request.sid
    client_session_id = data.get("session_id")

    if not is_valid_session(client_session_id):
        flask_socketio.emit(
            "invalid_session",
            {"message": "Session is invalid. Please reconnect."},
            room=subject_id,
        )
        return

    game_id = data["room"]

    game = GAMES.get(game_id, None)

    if game is None:
        return

    # Set the event for the corresponding player
    try:
        RESET_EVENTS[game_id][subject_id].send()
    except KeyError:
        logging.warning(
            f"KeyError in RESET_EVENTS for game {game_id}, subject {SUBJECT_ID_MAP[subject_id]}"
        )

    # Check if all players have completed their reset
    if all(event.ready() for event in RESET_EVENTS[game_id].values()):
        game.reset_event.send()  # Signal to the game loop that reset is complete


@socketio.on("ping")
def pong(data):
    sid = flask.request.sid
    socketio.emit(
        "pong",
        {
            "max_latency": CONFIG.max_ping,
            "min_ping_measurements": CONFIG.min_ping_measurements,
        },
        room=flask.request.sid,
    )

    # also track if the user isn't focused on their window.
    game = _get_existing_game(sid)
    if game is None:
        return

    document_in_focus = data["document_in_focus"]
    ping_ms = data["ping_ms"]
    player_name = SUBJECT_ID_MAP[sid]
    game.update_document_focus_status_and_ping(
        player_identifier=player_name,
        hidden_status=document_in_focus,
        ping=ping_ms,
    )


def run_game(game: remote_game.RemoteGame):
    end_status = [remote_game.GameStatus.Inactive, remote_game.GameStatus.Done]

    with game.lock:
        game.reset()

        if CONFIG.callback is not None:
            CONFIG.callback.on_episode_start(game)

    render_game(game)

    if CONFIG.input_mode == configuration_constants.InputModes.PressedKeys:
        socketio.emit("request_pressed_keys", {})

    eventlet.sleep(1 / game.config.fps)

    while game.status not in end_status:

        with game.lock:
            if CONFIG.callback is not None:
                CONFIG.callback.on_game_tick_start(game)
            game.tick()

            if CONFIG.callback is not None:
                CONFIG.callback.on_game_tick_end(game)

        render_game(game)
        if CONFIG.input_mode == configuration_constants.InputModes.PressedKeys:
            socketio.emit("request_pressed_keys", {})
        socketio.sleep(1 / game.config.fps)

        if (
            game.status == remote_game.GameStatus.Reset
            or game.status == remote_game.GameStatus.Done
        ):
            if CONFIG.callback is not None:
                CONFIG.callback.on_episode_end(game)

        if game.status == remote_game.GameStatus.Reset:
            eventlet.sleep(CONFIG.reset_freeze_s)
            socketio.emit(
                "game_reset",
                {
                    "timeout": CONFIG.reset_timeout,
                    "config": CONFIG.to_dict(serializable=True),
                    "room": game.game_id,
                },
                room=game.game_id,
            )

            game.reset_event.wait()

            # Replace the events for each player with new eventlet.event.Event instances
            for player_id in RESET_EVENTS[game.game_id].keys():
                RESET_EVENTS[game.game_id][player_id] = eventlet.event.Event()

            # Clear the game reset event
            game.set_reset_event()

            with game.lock:
                game.reset()
                if CONFIG.callback is not None:
                    CONFIG.callback.on_episode_start(game)

            render_game(game)

            socketio.sleep(1 / game.config.fps)

    with game.lock:
        logger.info(
            f"Game loop ended for {game.game_id}, ending and cleaning up."
        )
        if game.status != remote_game.GameStatus.Inactive:
            game.tear_down()

        if CONFIG.callback is not None:
            CONFIG.callback.on_game_end(game)
        socketio.emit(
            "end_game",
            {},
            room=game.game_id,
        )
        for human_player_name in game.human_players.values():
            PROCESSED_SUBJECT_NAMES.append(human_player_name)

        # _cleanup_game(game)


@socketio.on("end_game_request_redirect")
def on_request_redirect(data):
    subject_id = flask.request.sid

    waitroom_timeout = data.get("waitroom_timeout", False)
    if waitroom_timeout:
        redirect_url = CONFIG.waitroom_timeout_redirect_url
    else:
        redirect_url = CONFIG.experiment_end_redirect_url

    if CONFIG.append_subject_id_to_redirect:
        redirect_url += SUBJECT_ID_MAP[subject_id]

    # del SUBJECT_ID_MAP[subject_id]

    socketio.emit(
        "end_game_redirect",
        {
            "redirect_url": redirect_url,
            "redirect_timeout": CONFIG.redirect_timeout,
        },
        room=subject_id,
    )


def render_game(game: remote_game.RemoteGame):
    state = None
    encoded_image = None
    if CONFIG.env_to_state_fn is not None:
        # generate a state object representation
        state = CONFIG.env_to_state_fn(game.env, CONFIG)
    else:
        # Generate a base64 image of the game and send it to display
        assert (
            cv2 is not None
        ), "Must install cv2 to use default image rendering!"
        assert (
            game.env.render_mode == "rgb_array"
        ), "Env must be using render mode `rgb_array`!"
        game_image = game.env.render()
        _, encoded_image = cv2.imencode(".png", game_image)
        encoded_image = base64.b64encode(encoded_image).decode()

    hud_text = (
        CONFIG.hud_text_fn(game) if CONFIG.hud_text_fn is not None else None
    )

    # TODO(chase): this emits the same state to every player in a room, but we may want
    #   to have different observations for each player. Figure that out (maybe state is a dict
    #   with player_ids and their respective observations?).
    socketio.emit(
        "environment_state",
        {
            "game_state_objects": state,
            "game_image_base64": encoded_image,
            "step": game.tick_num,
            "hud_text": hud_text,
        },
        room=game.game_id,
    )


def on_exit():
    # Force-terminate all games on server termination
    for game_id in GAMES:
        game = _get_existing_game(game_id)
        if game is not None and CONFIG.callback is not None:
            CONFIG.callback.on_game_end(game)

        socketio.emit("end_game", {}, room=game_id)


def periodic_log() -> None:
    """Log information at specified 30s interval"""
    while True:
        logger.info(
            f"{time.ctime(time.time())}, there are {len(ACTIVE_GAMES)} active games, {len(WAITING_GAMES)} waiting games, {len(GAMES)} total games, and {len(SUBJECTS)} participants."
        )
        eventlet.sleep(30)


def run(config):
    global app, CONFIG, FREE_IDS, MAX_CONCURRENT_GAMES, logger
    CONFIG = config
    MAX_CONCURRENT_GAMES = CONFIG.max_concurrent_games

    # Global queue of available IDs. This is how we sync game creation and keep track of how many games are in memory
    FREE_IDS = queue.Queue(maxsize=CONFIG.max_concurrent_games)

    logger = setup_logger(__name__, CONFIG.logfile)

    # Initialize our game ID tracking data
    for _ in range(CONFIG.max_concurrent_games):
        add_new_game_id()

    atexit.register(on_exit)

    eventlet.spawn_n(periodic_log)

    socketio.run(
        app,
        log_output=app.config["DEBUG"],
        port=CONFIG.port,
        host=CONFIG.host,
    )
