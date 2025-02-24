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
from interactive_gym.scenes import unity_scene
from interactive_gym.scenes import static_scene
from interactive_gym.scenes import scene

from interactive_gym.configurations import (
    configuration_constants,
)

# Define the start scene, which is the landing page for participants.
start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="footsies_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body=(
            "Welcome to the Footsies experiment! This is a demonstration of "
            "how to set up an experiment with a WebGL-based Unity environment in Interactive Gym.",
        ),
    )
)


footsies_scene = (
    unity_scene.UnityScene()
    .scene(scene_id="footsies_scene_0", experiment_config={})
    .webgl(
        build_name="footsies_webgl_0224",
        height=1080 / 3,
        width=1960 / 3,
    )
)

stager = stager.Stager(
    scenes=[
        start_scene,
        footsies_scene,
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
        .experiment(stager=stager, experiment_id="footsies_test")
        .hosting(port=5704, host="0.0.0.0")
    )

    app.run(experiment_config)
