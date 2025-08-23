"""
This is a self-contained example of launching an Interactive Gym experiment with the
CoGrid Search and Rescue environment:

https://cogrid.readthedocs.io/en/latest/content/examples.html#module-cogrid.envs.search_rescue.search_rescue

"""

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
from interactive_gym.scenes import static_scene, gym_scene
from interactive_gym.configurations import experiment_config

from interactive_gym.configurations import (
    configuration_constants,
)


start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="search_rescue_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body="Welcome to the Search and Rescue environment demo!",
    )
)


MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6

# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "q": Toggle,
}

TILE_SIZE = 45
search_rescue_gym_scene = (
    gym_scene.GymScene()
    .scene(scene_id="cramped_room_sp_0", experiment_config={})
    .policies(policy_mapping={0: "human", 1: "random"}, frame_skip=5)
    .rendering(
        fps=30,
        game_width=TILE_SIZE * 7,
        game_height=TILE_SIZE * 6,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=1,
        max_steps=1350,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "This is an example environment using the Search and Rescue tak."
        "When the button activates, click it to begin. "
        "</p></center>",
        in_game_scene_body="""
        <center>
        <p>
        TODO: Add controls description.
        </p>
        </center>
        <br><br>
        """,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_filepath="interactive_gym/examples/cogrid/search_rescue_env_initialization.py",
        packages_to_install=["numpy", "cogrid==0.0.16"],
    )
)

end_scene = (
    static_scene.EndScene()
    .scene(
        scene_id="search_rescue_end_scene",
        should_export_metadata=True,
        experiment_config={},
    )
    .display(
        scene_header="Thank you for playing!",
        scene_body="You've completed the demo.",
    )
)

stager = stager.Stager(
    scenes=[
        start_scene,
        search_rescue_gym_scene,
        end_scene,
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5704, help="Port number to listen on"
    )
    args = parser.parse_args()

    experiment_config = (
        experiment_config.ExperimentConfig()
        .experiment(stager=stager, experiment_id="sr_test")
        .hosting(port=5704, host="0.0.0.0")
    )

    app.run(experiment_config)
