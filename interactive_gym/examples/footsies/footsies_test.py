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


footsies_initial_survey_scene = (
    static_scene.ScalesAndTextBox(
        scale_questions=[
            "I play video games frequently.",
            "I have experience playing fighting games (Street Fighter, Tekken, etc.).",
            "I know the fundamental strategies of fighting games.",
        ],
        pre_scale_header="",
        scale_labels=[
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
        ],
        text_box_header="Please leave any additional comments about your experience with fighting games. Write N/A if you do not have anything to add.",
        scale_size=7,
    )
    .scene(scene_id="footsies_initial_survey_0", experiment_config={})
    .display(scene_subheader="Initial Survey")
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
        preload_game=True,
    )
    .game(
        num_episodes=5 // EPISODES_SCALE_DOWN,
        score_fn=lambda data: int(data["winner"] == "P1"),
    )
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
    .game(
        num_episodes=25 // EPISODES_SCALE_DOWN,
        score_fn=lambda data: int(data["winner"] == "P1"),
    )
)

footsies_training_survey_scene = (
    static_scene.ScalesAndTextBox(
        scale_questions=[
            "My skills improved over the course of playing with my training partner.",
            "My training partner was effective in helping me learn a good strategy.",
            "My training partner was fun to play against.",
            "My training partner felt...",
        ],
        pre_scale_header="",
        scale_labels=[
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Too Easy to Beat", "Evenly Matched", "Too Hard to Beat"],
        ],
        text_box_header="Please describe the general strategy you've learned from your training partner. What is your approach to winning? What would have made the CPU a better training partner?",
        scale_size=7,
    )
    .scene(scene_id="footsies_survey_0", experiment_config={})
    .display(
        scene_subheader="Feedback About Your CPU Training Partner",
        scene_header="Training Survey 1/2",
    )
)

footsies_mc_survey = static_scene.MultipleChoice(
    pre_questions_header="""
    In this survey, we'll ask about what you learned about the game. Specifically in how controls result in particular actions in the game. Please select all that apply for each option. 
    You will earn an aditional bonus of $0.10 for each question that you answer correctly.
    <br>
    <br>
    The answer correspond to key press sequence or single pressses. For example 
    <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>
    means pressing the "D" key followed by the space bar. On the other hand, <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> means
    pressing the "D" key and the space bar at the same time. 
    """,
    questions=[
        "What key press(es) result in this movement?",
        "What key press(es) result in this movement?",
        "What key press(es) result in this attack?",
        "What key press(es) result in this attack?",
        "What key press(es) result in this attack?",
        "What key press(es) result in this attack?",
        "What key press(es) result in this attack?",
        "What key press(es) result in this attack?",
    ],
    choices=[
        [
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> -> <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
        [
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released)",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'> (Held then released) + <img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-d-key-50.png' alt='D key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
            "<img src='static/assets/keys/icons8-a-key-50.png' alt='A key' height='24' width='24' style='vertical-align:middle;'> + <img src='static/assets/keys/icons8-space-key-50.png' alt='Space key' height='24' width='24' style='vertical-align:middle;'>",
        ],
    ],
    images=[
        "static/assets/footsies/gifs/backward_dash.gif",
        "static/assets/footsies/gifs/forward_dash.gif",
        "static/assets/footsies/gifs/kick_ko.gif",
        "static/assets/footsies/gifs/kick_no_ko.gif",
        "static/assets/footsies/gifs/knee_no_ko.gif",
        "static/assets/footsies/gifs/low_kick.gif",
        "static/assets/footsies/gifs/uppercut_miss.gif",
        "static/assets/footsies/gifs/uppercut.gif",
    ],
    multi_select=True,
).display(scene_header="Training Survey 2/2")

footsies_test_scene = (
    unity_scene.UnityScene()
    .display(
        scene_header="Footsies",
        scene_subheader="""
        <div style="text-align: center; font-family: 'Press Start 2P', cursive; padding: 8px;">
            <p style="color: #000; text-shadow: 2px 2px #FFF; margin: 5px;">FINAL CHALLENGE</p>
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
    .game(
        num_episodes=20 // EPISODES_SCALE_DOWN,
        score_fn=lambda data: int(data["winner"] == "P1"),
    )
)


footsies_end_survey_scene = (
    static_scene.ScalesAndTextBox(
        scale_questions=[
            "The strategy I learned from my training partner was effective against the final challenge opponents.",
            "The final challenge opponents were fun to play against.",
            "The final challenge opponents felt...",
        ],
        pre_scale_header="",
        scale_labels=[
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
            ["Too Easy to Beat", "Evenly Matched", "Too Hard to Beat"],
        ],
        text_box_header="Please describe any additional reasoning for your selections or thoughts on the study. You may write N/A if you do not have any anything to add.",
        scale_size=7,
    )
    .scene(scene_id="footsies_survey_0", experiment_config={})
    .display(scene_subheader="Feedback About Your CPU Training Partner")
)


footsies_end_scene = (
    static_scene.CompletionCodeScene()
    .scene(
        scene_id="footsies_end_completion_code_scene",
        should_export_metadata=True,
        experiment_config={},
    )
    .display(
        scene_header="Thank you for participating!",
    )
)


stager = stager.Stager(
    scenes=[
        start_scene,
        # footsies_initial_survey_scene,
        footsies_tutorial_scene,
        footsies_initial_scene,
        footsies_training_scene,
        footsies_training_survey_scene,
        footsies_mc_survey,
        footsies_test_scene,
        footsies_end_survey_scene,
        footsies_end_scene,
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
