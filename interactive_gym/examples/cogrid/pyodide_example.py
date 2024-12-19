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


tutorial_gym_scene = (
    gym_scene.GymScene()
    .scene(
        scene_id="overcooked_tutorial",
        experiment_config={},
    )
    .policies(
        policy_mapping={
            0: configuration_constants.PolicyTypes.Human,
        },
    )
    .rendering(
        fps=30,
        env_to_state_fn=overcooked_utils.overcooked_env_to_render_fn,
        assets_to_preload=overcooked_utils.overcooked_preload_assets_spec(),
        hud_text_fn=overcooked_utils.hud_text_fn,
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 6,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=1,
        max_steps=1000,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked Tutorial",
        scene_body_filepath="interactive_gym/server/static/templates/overcooked_controls.html",
        in_game_scene_body="""
        <center>
        <p>
        Use the arrow keys <img src="static/assets/keys/arrow_keys_2.png" alt="Keyboard arrow keys" height="24" width="20" style="vertical-align:middle;"> 
        to control your chef <img src="static/assets/overcooked/blue_chef.png" alt="Blue Chef" height="24" width="24" style="vertical-align:middle;"> 
        and press <img src="static/assets/keys/icons8-w-key-50.png" alt="W key" height="24" width="24" style="vertical-align:middle;"> to pick up and 
        drop objects. Try to deliver as many dishes as possible by combining onions in the pot, plating the cooked onions, 
        and delivering them to the grey delivery zone.
        </p>
        </center>
        <br><br>
        """,
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_filepath="interactive_gym/examples/cogrid/pyodide_overcooked/env_initialization/tutorial_cramped_room_environment_initialization.py",
        packages_to_install=["numpy", "cogrid==0.0.9", "opencv-python"],
    )
)


base_fixed_eval_ = (
    static_scene.Scales(
        scale_questions=[
            "My partner was enjoyable to work with.",
            "My partner's behavior was predictable.",
            "My partner was effective as a teammate.",
        ],
        scale_labels=[
            ["Strongly Disagree", "Neutral", "Strongle Agree"],
        ],
        text_box_header="...",
    )
    .scene(scene_id="cramped_room_fixed_eval_", experiment_config={})
    .display(scene_subheader="Feedback About Your AI Partner")
)

gym_scene = (
    gym_scene.GymScene()
    .scene(scene_id="my_gym_scene", experiment_config={})
    .policies(
        policy_mapping={0: Human, 1: "model.onnx"},
    )
    .rendering([...])
    .gameplay([...])
    .user_experience([...])
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_="""
            from cogrid import registry
            env = registry.make("Overcooked-CrampedRoom-v0)
            env
""",
        packages_to_install=["cogrid==0.0.9"],
    )
)


start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="overcooked_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body_filepath="interactive_gym/server/static/templates/overcooked_demo_instructions.html",
    )
)

end_scene = (
    static_scene.EndScene()
    .scene(
        scene_id="end_completion_code_scene",
        should_export_metadata=True,
        experiment_config={},
    )
    .display(
        scene_header="Thank you for playing!",
        scene_body="You've completed the demo",
    )
)

stager = stager.Stager(
    scenes=[
        start_scene,
        gym_scene,
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
        .experiment(stager=stager, experiment_id="overcooked_test")
        .hosting(port=5704, host="0.0.0.0")
    )

    app.run(experiment_config)
