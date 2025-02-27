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
from interactive_gym.examples.footsies import footsies_scene

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
        scene_body_filepath="interactive_gym/examples/footsies/static/introduction.html",
    )
)

footsies_tutorial_scene = (
    static_scene.StaticScene()
    .scene("footsies_tutorial_scene")
    .display(
        scene_header="Footsies Tutorial",
        scene_body_filepath="interactive_gym/examples/footsies/static/tutorial_static.html",
    )
)

CONTROLS_SUBHEADER = """ 
        <div style="text-align: center; font-family: 'Press Start 2P', cursive; padding: 8px; color: #000;">
        <p style="margin: 10px;">
        MOVE WITH <img src="static/assets/keys/icons8-a-key-50.png" alt="A key" height="24" width="24" style="vertical-align:middle;"> AND <img src="static/assets/keys/icons8-d-key-50.png" alt="D key" height="24" width="24" style="vertical-align:middle;">
        </p>
        <p style="margin: 5px;">
        ATTACK WITH THE SPACE BAR <img src="static/assets/keys/icons8-space-key-50.png" alt="Space key" height="24" width="24" style="vertical-align:middle;">
        </p>
        </div>
"""


EPISODES_SCALE_DOWN = 1

footsies_initial_scene = (
    unity_scene.UnityScene()
    .display(
        scene_header="Footsies",
        scene_subheader="""
        <div style="text-align: center; font-family: 'Press Start 2P', cursive; padding: 8px;">
            <p style="color: #000; text-shadow: 2px 2px #FFF; margin: 5px;">INITIAL CHALLENGE</p>
        </div>
        """
        + CONTROLS_SUBHEADER,
    )
    .scene(scene_id="footsies_initial_eval_0", experiment_config={})
    .webgl(
        build_name="footsies_webgl_a613788",
        height=1080 / 3,
        width=1960 / 3,
    )
    .game(num_episodes=5 // EPISODES_SCALE_DOWN)
)

footsies_training_scene = (
    unity_scene.UnityScene()
    .display(
        scene_header="Footsies",
        scene_subheader="""
        <div style="text-align: center; font-family: 'Press Start 2P', cursive; padding: 8px;">
            <p style="color: #000; text-shadow: 2px 2px #FFF; margin: 5px;">TRAINING ROUNDS</p>
            <p style="color: #000; margin: 5px;">HONE YOUR SKILLS WITH AN AI PARTNER</p>
            <p style="color: #FF0000; margin: 5px;">25 ROUNDS</p>
        </div>
        """
        + CONTROLS_SUBHEADER,
    )
    .scene(scene_id="footsies_training_0", experiment_config={})
    .webgl(
        build_name="footsies_webgl_a613788",
        height=1080 / 3,
        width=1960 / 3,
    )
    .game(num_episodes=25 // EPISODES_SCALE_DOWN)
)


footsies_survey_scene = (
    static_scene.ScalesAndTextBox(
        scale_questions=[
            "My partner was effective in helping me learn.",
            "My partner was fun to play against.",
            "My partner was...",
        ],
        pre_scale_header="",
        scale_labels=[
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Too Easy to Beat", "Evenly Matched", "Too Hard to Beat"],
        ],
        text_box_header="Please describe any additional reasoning for your selections. This might include specific actions or behaviors. You may write N/A if you do not have any anything to add.",
    )
    .scene(scene_id="footsies_survey_0", experiment_config={})
    .display(scene_subheader="Feedback About Your AI Training Partner")
)


footsies_test_scene = (
    unity_scene.UnityScene()
    .display(
        scene_header="Footsies",
        scene_subheader="""
        <div style="text-align: center; font-family: 'Press Start 2P', cursive; padding: 8px;">
            <p style="color: #000; text-shadow: 2px 2px #FFF; margin: 5px;">FINAL CHALLENGE</p>
            <p style="color: #000; margin: 5px;">PROVE YOUR WORTH!</p>
            <p style="color: #000; margin: 5px;">WIN $0.50 FOR EACH VICTORY</p>
            <p style="color: #FF0000; margin: 5px;">10 ROUNDS</p>
        </div>
        """
        + CONTROLS_SUBHEADER,
    )
    .scene(scene_id="footsies_scene_0", experiment_config={})
    .webgl(
        build_name="footsies_webgl_a613788",
        height=1080 / 3,
        width=1960 / 3,
    )
    .game(num_episodes=20 // EPISODES_SCALE_DOWN)
)

stager = stager.Stager(
    scenes=[
        start_scene,
        footsies_tutorial_scene,
        # footsies_initial_scene,
        # footsies_training_scene,
        # footsies_survey_scene,
        footsies_test_scene,
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
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
