import base64
import io
import logging
import os
import threading
import json

from PIL import Image
import flask
import flask_socketio
import pygame
import numpy as np
from flask_cors import CORS

try:
    import cv2
except ImportError:
    cv2 = None
    logging.warn(
        "cv2 not installed. This is required if you're not "
        "defining a rendering function and want to (inefficiently) "
        "have the canvas display whatever is returned from `env.render()`."
    )


from interactive_framework import remote_game, policy_wrapper
import remote_config

CONFIG = remote_config.RemoteConfig()

# Data structure to save subjects by their socket id
SUBJECTS = {}

# Data structure to save subjects games in memory OBJECTS by their socket id
GAMES = {}

app = flask.Flask(__name__, template_folder=os.path.join("static", "templates"))
CORS(app)
app.config["SECRET_KEY"] = "secret!"

app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"
socketio = flask_socketio.SocketIO(
    app, cors_allowed_origins="*", logger=app.config["DEBUG"]
)

cur_state = None


@app.route("/<subject_name>")
def index(subject_name):
    print("index")
    return flask.render_template(
        "index.html",
        async_mode=socketio.async_mode,
        start_header_text=CONFIG.start_header_text,
        start_page_text=CONFIG.start_page_text,
        game_header_text=CONFIG.game_header_text,
        game_page_text=CONFIG.game_page_text,
    )


@socketio.on("connect")
def on_connect():
    subject_socket_id = flask.request.sid

    if subject_socket_id in SUBJECTS:
        return

    SUBJECTS[subject_socket_id] = threading.Lock()


@socketio.on("disconnect")
def on_disconnect():
    print("on disconnect")
    subject_socket_id = flask.request.sid
    if subject_socket_id in SUBJECTS:
        del SUBJECTS[subject_socket_id]
    if subject_socket_id in GAMES:
        del GAMES[subject_socket_id]


@socketio.on("request_config")
def send_config(*args):
    config = CONFIG.to_dict(serializable=True)
    socketio.emit("send_config", {"config": json.dumps(config)})


@socketio.on("create_join")
def on_create_join(data):
    subject_socket_id = flask.request.sid
    with SUBJECTS[subject_socket_id]:
        flask_socketio.join_room(subject_socket_id)
        env = CONFIG.env_creator(render_mode="rgb_array")  # human
        policy_handler = policy_wrapper.MultiAgentPolicyWrapper(
            policy_mapping=CONFIG.policy_mapping,
            available_policies=CONFIG.available_policies,
            action_space=env.action_space,
            configs=CONFIG.policy_configs,
        )
        game = remote_game.RemoteGame(
            env,
            human_agent_id=CONFIG.human_id,
            policy_handler=policy_handler,
            seed=CONFIG.seed,
        )
        game.id = subject_socket_id
        GAMES[subject_socket_id] = game
        socketio.start_background_task(play_game, game)


@socketio.on("send_pressed_keys")
def on_action(data):
    subject_socket_id = flask.request.sid
    game = GAMES[subject_socket_id]

    pressed_keys = data["pressed_keys"]

    if not game or not any([k in CONFIG.action_mapping for k in pressed_keys]):
        return

    action = None
    for k in pressed_keys:
        if k in CONFIG.action_mapping:
            action = k
            break

    assert action is not None

    game.pending_actions.put(CONFIG.action_mapping[action])


def play_game(game: remote_game.RemoteGame):
    clock = pygame.time.Clock()
    episodes_done = 0
    game.reset(game.seed)
    socketio.emit("start_game")
    while not episodes_done == CONFIG.num_episodes:
        # Tell the server that we want to receive actions at the next update.
        socketio.emit("request_pressed_keys", {"data": "Server requests key data"})

        clock.tick(CONFIG.fps)

        if game.is_multiagent:
            actions = {agent_id: CONFIG.default_action for agent_id in game.agent_ids}
        else:
            actions = CONFIG.default_action

        if game.is_multiagent:
            for a_id, obs in game.obs.items():
                if a_id == game.human_agent_id:
                    continue

                if game.env.t % CONFIG.frame_skip == 0:
                    actions[a_id] = game.policy_handler.compute_single_action(
                        obs=obs, agent_id=a_id
                    )

        elif not game.human_agent_id and game.t % CONFIG.frame_skip == 0:
            actions = game.policy_handler.compute_single_action(game.obs)

        if game.human_agent_id and game.pending_actions.qsize() != 0:
            human_action = game.pending_actions.get(block=False)
        else:
            human_action = CONFIG.default_action

        if game.is_multiagent:
            actions[game.human_agent_id] = human_action
        else:
            actions = human_action

        game.step(actions)
        if not game.is_done:
            render_game(game=game)
        else:
            # end of episode
            episodes_done = episodes_done + 1
            if not episodes_done == CONFIG.num_episodes:
                game.reset(game.seed)
                socketio.emit("game_episode_start")

    socketio.emit("game_ended", {"url": CONFIG.redirect_url})


def render_game(game: remote_game.RemoteGame):

    state = None
    encoded_image = None
    if CONFIG.env_to_state_fn is not None:
        state = CONFIG.env_to_state_fn(game.env)
    else:
        assert cv2 is not None, "Must install cv2 to use default image rendering!"
        game_image = game.env.render()
        _, encoded_image = cv2.imencode(".png", game_image)

        # Convert the encoded image to Base64 string
        encoded_image = base64.b64encode(encoded_image).decode()

    socketio.emit(
        "environment_state",
        {
            "state": state,
            "game_image_base64": encoded_image,
            "rewards": game.cumulative_reward,
            "step": game.t,
        },
        room=game.id,
    )


def run(config):
    global CONFIG
    CONFIG = config

    socketio.run(
        app,
        log_output=app.config["DEBUG"],
        port=CONFIG.port,
        host=CONFIG.host,
        allow_unsafe_werkzeug=True,
    )
