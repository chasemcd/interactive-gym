from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from interactive_gym.server import app
from interactive_gym.scenes import stager

from interactive_gym.configurations import experiment_config
from interactive_gym.scenes import scene


from interactive_gym.examples.footsies import scenes


stager = stager.Stager(
    scenes=[
        scenes.start_scene,
        # scenes.footsies_initial_survey_scene,
        # scenes.footsies_tutorial_scene,
        # scenes.footsies_initial_scene,
        # scenes.footsies_initial_challenge_survey_scene,
        scene.RandomizeOrder(
            [
                # scenes.footsies_dynamic_difficulty_scene,
                scenes.footsies_controllable_difficulty_scene,
                # scenes.footsies_fixed_high_skill_scene,
            ],
            keep_n=1,
        ),
        scenes.footsies_training_survey_scene,
        scenes.footsies_mc_survey,
        scenes.footsies_test_scene,
        scenes.footsies_end_survey_scene,
        scenes.footsies_end_scene,
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
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
