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


# Update the agent IDs to match the environment
# e.g., [adversary_0, adversary_1, ...]
# [adversary_0, adversary_1, adversary_2, agent_0]
POLICY_MAPPING = {
    "adversary_0": configuration_constants.PolicyTypes.Random,
    "adversary_1": configuration_constants.PolicyTypes.Random,
    "adversary_2": configuration_constants.PolicyTypes.Random,
    "agent_0": configuration_constants.PolicyTypes.Random,
}


# TODO: What are the actual values? Check these to make sure they are correct!
NOOP = 0
LEFT = 1
RIGHT = 2
DOWN = 3
UP = 4

# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
ACTION_MAPPING = {
    "ArrowLeft": LEFT,
    "ArrowUp": UP,
    "ArrowRight": RIGHT,
    "ArrowDown": DOWN,
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
            "Welcome to the simple tag experiment! This is a demonstration of "
            "how to set up a basic experiment with a human and AI interacting together.",
        ),
    )
)


mpe_scene = (
    gym_scene.GymScene()
    .scene(scene_id="mpe_gym_scene", experiment_config={})
    .policies(policy_mapping=POLICY_MAPPING, frame_skip=1)
    .rendering(
        fps=30,
        game_width=600,
        game_height=250,
    )
    .gameplay(
        default_action=NOOP,
        action_mapping=ACTION_MAPPING,
        num_episodes=5,
        max_steps=200,
        input_mode=configuration_constants.InputModes.PressedKeys,
    )
    .user_experience(
        scene_header="MPE Tag",
        scene_body="<center><p>" "Press start to continue. " "</p></center>",
        in_game_scene_body="""
        <center>
        <p>
        Use the arrow keys to move!
        </p>
        </center>
        <br><br>
        """,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_filepath="interactive_gym/examples/mpe/mpe_tag_initialization.py",
        packages_to_install=[
            "pettingzoo",
        ],
    )
)


stager = stager.Stager(
    scenes=[
        start_scene,
        mpe_scene,
        oc_scenes.end_scene,
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5703, help="Port number to listen on"
    )
    args = parser.parse_args()

    experiment_config = (
        experiment_config.ExperimentConfig()
        .experiment(stager=stager, experiment_id="mpe_tag_example")
        .hosting(port=5703, host="0.0.0.0")
    )

    app.run(experiment_config)
