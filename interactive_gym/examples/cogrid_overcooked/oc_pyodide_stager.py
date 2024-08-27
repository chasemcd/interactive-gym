from __future__ import annotations

import eventlet
import copy

eventlet.monkey_patch()

import argparse
from datetime import datetime

from cogrid.envs import registry

from interactive_gym.configurations import (
    configuration_constants,
    remote_config,
)
from interactive_gym.examples.cogrid_overcooked import (
    overcooked_callback,
    overcooked_utils,
)
from interactive_gym.server import app
from interactive_gym.scenes import gym_scene
from interactive_gym.scenes import static_scene
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager

from interactive_gym.configurations import experiment_config

MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


POLICY_MAPPING = {
    0: configuration_constants.PolicyTypes.Human,
    1: "static/assets/overcooked/models/recurrent_ibc_0.onnx",
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    return registry.make("Overcooked-RandomizedLayout-V0", render_mode=None)


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "q": Toggle,
}


with open(
    "interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/tutorial_cramped_room_environment_initialization.py"
) as f:
    tutorial_cr_env_initialization = f.read()

with open(
    "interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/cramped_room_environment_initialization.py"
) as f:
    cr_env_initialization = f.read()


with open(
    "interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/counter_circuit_environment_initialization.py"
) as f:
    cc_env_initialization = f.read()

start_scene = static_scene.StartScene(
    scene_id="start_scene", ig_config={}
).display(
    scene_header="Welcome",
    scene_body=(
        "To begin the experiment, please click the button below. You will first be brought to an instructions page "
        "that outlines the task you will be completing and provides a brief tutorial. "
        "After the tutorial, you will proceed through the experiment, where you will interact with different AI partners "
        "in a task and provide your preferences between interacting with two of them."
    ),
)


tutorial_gym_scene = (
    gym_scene.GymScene(scene_id="overcooked_tutorial", ig_config={})
    .policies(
        policy_mapping={
            0: configuration_constants.PolicyTypes.Human,
        },
    )
    .rendering(
        fps=30,
        env_to_state_fn=overcooked_utils.overcooked_env_to_render_fn,
        assets_to_preload=overcooked_utils.overcooked_preload_assets_spec(),
        hud_text_fn=overcooked_utils.hud_text_fn,
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 6,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=1,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked Tutorial",
        scene_body_filepath="interactive_gym/server/static/templates/overcooked_instructions.html",
        in_game_scene_body="""
        Use the arrow keys <img src="static/assets/keys/arrow_keys_2.png" alt="Keyboard arrow keys" height="24" width="20" style="vertical-align:middle;"> 
        to control your chef <img src="static/assets/overcooked/blue_chef.png" alt="Blue Chef" height="24" width="24" style="vertical-align:middle;"> 
        and press <img src="static/assets/keys/icons8-w-key-50.png" alt="W key" height="24" width="24" style="vertical-align:middle;"> to pick up and 
        drop objects. Try to deliver as many dishes as possible by combining onions in the pot, plating the cooked onions, 
        and delivering them to the grey delivery zone.
        <br><br>
        """,
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code=tutorial_cr_env_initialization,
        packages_to_install=["numpy", "cogrid==0.0.3"],
    )
)

cr_gym_scene_1 = (
    gym_scene.GymScene(scene_id="overcooked_randomized", ig_config={})
    .policies(policy_mapping=POLICY_MAPPING, frame_skip=5)
    .rendering(
        fps=30,
        env_to_state_fn=overcooked_utils.overcooked_env_to_render_fn,
        assets_to_preload=overcooked_utils.overcooked_preload_assets_spec(),
        hud_text_fn=overcooked_utils.hud_text_fn,
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 6,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=1,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked (Round 1/2)",
        scene_body="You'll now play with Partner 1 for a single round. This will be followed by a round with Partner 2. When the button turns green, click it to begin.",
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code=cr_env_initialization,
        packages_to_install=["numpy", "cogrid==0.0.3"],
    )
)

cr_gym_scene_2 = copy.deepcopy(cr_gym_scene_1).user_experience(
    scene_header="Overcooked (Round 1/2)",
    scene_body="You'll now play with Partner 2 on the same layout for a single round. After this round, you will provide your preference between the two partners. When the button turns green, click it to begin.",
    game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
)

options_scene_1 = static_scene.OptionBoxes(
    scene_id="options_scene_1", ig_config={}, options=["Partner 1", "Partner 2"]
).display(scene_header="Did you prefer Partner 1 or 2?")

cc_gym_scene_1 = (
    copy.deepcopy(cr_gym_scene_1)
    .pyodide(environment_initialization_code=cc_env_initialization)
    .user_experience(
        scene_header="Overcooked (2/2)",
        scene_body="You'll now play with Partner 1 for a single round. This will be followed by a round with Partner 2. When the button turns green, click it to begin.",
    )
    .rendering(
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 7,
    )
)

cc_gym_scene_2 = (
    copy.deepcopy(cc_gym_scene_1)
    .pyodide(environment_initialization_code=cc_env_initialization)
    .user_experience(
        scene_header="Overcooked (2/2)",
        scene_body="You'll now play with Partner 2 on the same layout for a single round. After this round, you will provide your preference between the two partners. When the button turns green, click it to begin.",
    )
)

options_scene_2 = static_scene.OptionBoxes(
    scene_id="options_scene_1", ig_config={}, options=["Partner 1", "Partner 2"]
).display(scene_header="Did you prefer Partner 1 or 2?")

end_scene = (
    static_scene.EndScene(scene_id="end_scene", ig_config={})
    .display(
        scene_header="Thank you for participating!",
        scene_body="The experiment is over. Please click the button below to be directed to a follow-up survey.",
    )
    .redirect(url="https://www.google.com")
)

stager = stager.Stager(
    scenes=[
        start_scene,
        tutorial_gym_scene,
        cr_gym_scene_1,
        cr_gym_scene_2,
        options_scene_1,
        cc_gym_scene_1,
        cc_gym_scene_2,
        options_scene_2,
        end_scene,
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5702, help="Port number to listen on"
    )
    args = parser.parse_args()

    ig_config = (
        experiment_config.ExperimentConfig()
        .experiment(stager=stager, experiment_id="overcooked_test")
        .hosting(port=5701, host="0.0.0.0")
    )

    app.run(ig_config)
