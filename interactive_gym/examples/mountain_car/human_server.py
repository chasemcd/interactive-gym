from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from interactive_gym.server import app
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager
from interactive_gym.examples.cogrid.pyodide_overcooked import (
    scenes as oc_scenes,
)
from interactive_gym.scenes import static_scene

from interactive_gym.configurations import experiment_config
from interactive_gym.scenes import gym_scene
from interactive_gym.scenes import static_scene
from interactive_gym.scenes import scene


from interactive_gym.configurations import (
    configuration_constants,
)

POLICY_MAPPING = {
    "agent_right": configuration_constants.PolicyTypes.Human,
    "agent_left": "static/assets/slime_volleyball/models/model.onnx",
}


LEFT_ACCELERATION = 0
NOOP_ACTION = 1
RIGHT_ACCELERATION = 2

# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": LEFT_ACCELERATION,
    "ArrowRight": RIGHT_ACCELERATION,
}


# Define the start scene, which is the landing page for participants.
start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="mountain_car_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body=(
            "Welcome to the Mountain Car experiment! This is a demonstration of "
            "how to set up a basic experiment with an environment that renders via an RGB image.",
        ),
    )
)


slime_sceme = (
    gym_scene.GymScene()
    .scene(scene_id="mountain_car_scene", experiment_config={})
    # .policies(policy_mapping=POLICY_MAPPING, frame_skip=5)
    .rendering(
        fps=30,
        game_width=400,
        game_height=300,
    )
    .gameplay(
        default_action=NOOP_ACTION,
        action_mapping=action_mapping,
        num_episodes=5,
        max_steps=3000,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Mountain Car",
        scene_body="<center><p>" "Press start to continue. " "</p></center>",
        in_game_scene_body="""
        <center>
        <p>
        Use the arrow keys to move the car to make it up the hill!
        </p>
        </center>
        <br><br>
        """,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code="""
import gymnasium

env = gymnasium.make("MountainCar-v0", render_mode="rgb_array")
env
        """,
        packages_to_install=[
            "swig",
            "gymnasium[box2d]",
        ],
    )
)


stager = stager.Stager(
    scenes=[
        start_scene,
        slime_sceme,
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
        .experiment(stager=stager, experiment_id="mountain_car_demo")
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
