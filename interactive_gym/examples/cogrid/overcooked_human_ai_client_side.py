from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from interactive_gym.server import app
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager
from interactive_gym.examples.cogrid.scenes import (
    scenes as oc_scenes,
)

from interactive_gym.configurations import experiment_config

stager = stager.Stager(
    scenes=[
        oc_scenes.start_scene,
        oc_scenes.tutorial_gym_scene,
        scene.RandomizeOrder(
            scenes=[
                oc_scenes.cramped_room_0,
                oc_scenes.counter_circuit_0,
                oc_scenes.forced_coordination_0,
                oc_scenes.asymmetric_advantages_0,
                oc_scenes.coordination_ring_0,
            ],
        ),
        oc_scenes.feedback_scene,
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
