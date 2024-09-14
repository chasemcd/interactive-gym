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
from interactive_gym.examples.cogrid_overcooked.pyodide_overcooked import (
    scenes as oc_scenes,
)


from interactive_gym.configurations import experiment_config

stager = stager.Stager(
    scenes=[
        oc_scenes.start_scene,
        # oc_scenes.tutorial_gym_scene,
        scene.RandomizeOrder(
            scenes=[
                oc_scenes.cramped_room_0,
                oc_scenes.cramped_room_1,
                oc_scenes.counter_circuit_0,
                oc_scenes.counter_circuit_1,
                oc_scenes.forced_coordination_0,
                oc_scenes.forced_coordination_1,
                oc_scenes.asymmetric_advantages_0,
                oc_scenes.asymmetric_advantages_1,
                oc_scenes.coordination_ring_0,
                oc_scenes.coordination_ring_1,
            ]
        ),
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
        .experiment(stager=stager, experiment_id="overcooked_test")
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
