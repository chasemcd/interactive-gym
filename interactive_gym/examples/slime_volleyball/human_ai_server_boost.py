from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from slime_volleyball import slimevolley_boost_env

from interactive_gym.server import app
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager
from interactive_gym.examples.cogrid.scenes import (
    scenes as oc_scenes,
)
from interactive_gym.scenes import static_scene

from interactive_gym.configurations import experiment_config
from interactive_gym.scenes import gym_scene
from interactive_gym.scenes import static_scene
from interactive_gym.scenes import scene
from interactive_gym.utils import onnx_inference_utils


from interactive_gym.configurations import (
    configuration_constants,
)


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    config = {
        "human_inputs": POLICY_MAPPING.get("agent_left")
        == configuration_constants.PolicyTypes.Human,
    }
    env = slimevolley_boost_env.SlimeVolleyBoostEnv(
        config=config, render_mode="rgb_array"
    )
    # TODO(chase): remove bug in the game where this isn't
    # included in the boost env
    env.render_mode = "rgb_array"
    return env


POLICY_MAPPING = {
    # "agent_right": configuration_constants.PolicyTypes.Human,
    "agent_right": "interactive_gym/server/static/assets/slime_volleyball/models/boost_model.onnx",
    "agent_left": configuration_constants.PolicyTypes.Human,
}

NOOP = 0
LEFT = 1
UPLEFT = 2
UP = 3
UPRIGHT = 4
RIGHT = 5
BOOST = 6
LEFT_BOOST = 7
UPLEFT_BOOST = 8
UP_BOOST = 9
UPRIGHT_BOOST = 10
RIGHT_BOOST = 11

# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
ACTION_MAPPING = {
    "ArrowLeft": LEFT,
    ("ArrowLeft", "ArrowUp"): UPLEFT,
    "ArrowUp": UP,
    ("ArrowRight", "ArrowUp"): UPRIGHT,
    "ArrowRight": RIGHT,
    " ": BOOST,
    ("ArrowLeft", " "): LEFT_BOOST,
    ("ArrowUp", " "): UP_BOOST,
    ("ArrowRight", " "): RIGHT_BOOST,
    ("ArrowLeft", "ArrowUp", " "): UPLEFT_BOOST,
    ("ArrowRight", "ArrowUp", " "): UPRIGHT_BOOST,
}

# Define the start scene, which is the landing page for participants.
start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="slimevb_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body=(
            "Welcome to the Slime Volleyball experiment! This is a demonstration of "
            "how to set up a basic experiment with a human and AI interacting together.",
        ),
    )
)


slime_scene = (
    gym_scene.GymScene()
    .environment(env_config={"human_inputs": True}, env_creator=env_creator)
    .scene(scene_id="slime_gym_scene", experiment_config={})
    .policies(
        policy_mapping=POLICY_MAPPING,
        frame_skip=1,
        policy_inference_fn=onnx_inference_utils.onnx_model_inference_fn,
        load_policy_fn=onnx_inference_utils.load_onnx_policy_fn,
    )
    .rendering(
        fps=30,
        game_width=168 * 4,
        game_height=84 * 4,
    )
    .gameplay(
        default_action=NOOP,
        action_mapping=ACTION_MAPPING,
        num_episodes=5,
        max_steps=3000,
        input_mode=configuration_constants.InputModes.PressedKeys,
    )
    .user_experience(
        scene_header="Slime Volleyball",
        scene_body="<center><p>" "Press start to continue. " "</p></center>",
        in_game_scene_body="""
        <center>
        <p>
        Use the arrow keys <img src="static/assets/keys/arrow_keys_2.png" alt="Keyboard arrow keys" height="24" width="20" style="vertical-align:middle;"> 
        to control the slime on the right! 
        </p>
        </center>
        <br><br>
        """,
    )
)


stager = stager.Stager(
    scenes=[
        start_scene,
        slime_scene,
        oc_scenes.end_scene,
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5702, help="Port number to listen on"
    )
    args = parser.parse_args()

    experiment_config = (
        experiment_config.ExperimentConfig()
        .experiment(stager=stager, experiment_id="slime_vb_demo")
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
