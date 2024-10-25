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
        controllable_scenes.control_tutorial_scene,
        controllable_scenes.cramped_room_controllable_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_controllable_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_controllable_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_controllable_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_fixed_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_fixed_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_fixed_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_fixed_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.cramped_room_fixed_0,
        controllable_scenes.cramped_room_controllable_eval_0,
        controllable_scenes.choice_cramped_room_0,
        controllable_scenes.cramped_room_controllable_eval_0,
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
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
