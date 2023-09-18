import base64
import io
import os
import threading

from PIL import Image
import flask
import flask_socketio
import pygame
import numpy as np

from interactive_framework import remote_game, policy_wrapper
import remote_config

CONFIG = remote_config.RemoteConfig()

# Data structure to save subjects by their socket id
SUBJECTS = {}

# Data structure to save subjects games in memory OBJECTS by their socket id
GAMES = {}

app = flask.Flask(__name__, template_folder=os.path.join("static", "templates"))
app.config["SECRET_KEY"] = "secret!"

app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"
socketio = flask_socketio.SocketIO(
    app, cors_allowed_origins="*", logger=app.config["DEBUG"]
)


@app.route("/<subject_name>")
def index(subject_name):
    print("index")
    return flask.render_template(
        "index.html",
        async_mode=socketio.async_mode,
        header_text=CONFIG.game_header_text,
        header_text_start=CONFIG.start_page_text,
    )


@socketio.on("connect")
def on_connect():
    print("on connect")
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


@socketio.on("create_join")
def on_create_join(data):
    print("on create join")
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


@socketio.on("action")
def on_action(data):
    subject_socket_id = flask.request.sid
    action = data["action"]
    step = data["step"]
    game = GAMES[subject_socket_id]
    print("Action {} for {}".format(action, step))
    if not game:
        return

    game.pending_actions.put(CONFIG.action_mapping[action])


def play_game(game: remote_game.RemoteGame):
    clock = pygame.time.Clock()
    episodes_done = 0
    game.reset(game.seed)
    socketio.emit("game_episode_start")
    while not episodes_done == CONFIG.num_episodes:

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

        game_render = game.step(actions)
        if game_render is not None:
            render_game_image(game_render, game=game)
        else:
            # end of episode
            episodes_done = episodes_done + 1
            if not episodes_done == CONFIG.num_episodes:
                game.reset(game.seed)
                socketio.emit("game_episode_start")

    socketio.emit("game_ended", {"url": CONFIG.redirect_url})


def render_game_image(image: np.ndarray, game: remote_game.RemoteGame):
    png_img = Image.fromarray(image, "RGB")
    im_file = io.BytesIO()
    png_img.save(im_file, format="png")
    im_bytes = im_file.getvalue()  # im_bytes: image in binary format.
    im_b64 = base64.b64encode(im_bytes)
    base64str = im_b64.decode("utf-8")

    socketio.emit(
        "game_board_update",
        {"state": base64str, "rewards": game.cumulative_reward, "step": game.t,},
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
