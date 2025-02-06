# from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from interactive_gym.server import app
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager
from interactive_gym.examples.cogrid.pyodide_overcooked import (
    controllable_scenes,
    scenes,
)

from interactive_gym.configurations import experiment_config

stager = stager.Stager(
    scenes=[
        controllable_scenes.start_scene,
        scenes.tutorial_gym_scene,
        controllable_scenes.tutorial_with_bot_scene,
        controllable_scenes.control_tutorial_scene,
        controllable_scenes.end_tutorial_static_scene,
        scene.RandomizeOrder(
            [
                controllable_scenes.SCENES_BY_LAYOUT["counter_circuit"],
                controllable_scenes.SCENES_BY_LAYOUT["forced_coordination"],
                controllable_scenes.SCENES_BY_LAYOUT["asymmetric_advantages"],
                controllable_scenes.SCENES_BY_LAYOUT["coordination_ring"],
                controllable_scenes.SCENES_BY_LAYOUT["cramped_room"],
            ],
            keep_n=2,
        ),
        controllable_scenes.end_scene,
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
        .experiment(stager=stager, experiment_id="overcooked_controllable")
        .hosting(port=5704, host="0.0.0.0")
    )

    app.run(experiment_config)
