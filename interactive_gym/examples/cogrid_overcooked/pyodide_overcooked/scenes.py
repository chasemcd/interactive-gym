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

from interactive_gym.configurations import experiment_config


# Constants for controls/actions/etc.
MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


SP_POLICY_MAPPING = {
    0: configuration_constants.PolicyTypes.Human,
    1: "static/assets/overcooked/models/sp_encoding_00.onnx",
}

IBC_POLICY_MAPPING = {
    0: configuration_constants.PolicyTypes.Human,
    1: "static/assets/overcooked/models/ibc_encoding_01.onnx",
}


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "W": PickupDrop,
    "q": Toggle,
    "Q": Toggle,
}


# Define the start scene, which is the landing page for participants.
start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="overcooked_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body_filepath="interactive_gym/server/static/templates/overcooked_instructions.html",
    )
)


# Now define the tutorial gym scene, where we teach participants how to play.
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
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/tutorial_cramped_room_environment_initialization.py",
        packages_to_install=["numpy", "cogrid==0.0.8", "opencv-python"],
    )
)


cramped_room_sp_0 = (
    gym_scene.GymScene()
    .scene(scene_id="cramped_room_sp_0", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING, frame_skip=5)
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
        max_steps=1350,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play with a partner for a single round. "
        "This will be followed by a round with a different partner "
        "in the same environment layout."
        "<br><br> "
        "You will be playing on the layout pictured below. "
        '<center><img src="static/assets/overcooked/cramped_room.png" alt="Annotated Overcooked environment." height="270" width="315"></center>'
        "When the button activates, click it to begin. "
        "</p></center>",
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
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
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/cramped_room_environment_initialization.py",
        packages_to_install=["numpy", "cogrid==0.0.8", "opencv-python"],
    )
)
cramped_room_ibc_1 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="cramped_room_ibc_1", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
)

cramped_room_ibc_0 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="cramped_room_ibc_0", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play another round on the same layout. "
        "After this round, you will provide your preference "
        "between the two partners you interacted with. "
        "When the button activates, click it to begin. "
        "</p></center>",
    )
)
cramped_room_sp_1 = (
    copy.deepcopy(cramped_room_ibc_0)
    .scene(scene_id="cramped_room_sp_1", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING)
)

cramped_room_options_scene_0 = (
    static_scene.OptionBoxesWithScalesAndTextBox(
        options=["First Partner", "Second Partner"],
        scale_questions=[
            "My partner and I coordinated our actions well together.",
            "My partner perceived accurately what tasks I was trying to accomplish.",
            "I was able to understand and predict what tasks my partner was trying to accomplish.",
            "My partner felt human-like.",
        ],
        pre_scale_header="Now, please indicate the relative extent to which you agree with the following statements about each partner. Move the slider to the left if the statement holds more for the first partner, and to the right for the second partner.",
        scale_labels=["First Partner", "No Difference", "Second Partner"],
        text_box_header="Please describe any additional reasoning for your preference. This might include specific actions or behaviors that you liked or disliked. You may write N/A if you do not have any anything to add.",
        option_box_header="Did you prefer your first or second partner?",
    )
    .scene(scene_id="cramped_room_options_scene_0", experiment_config={})
    .display(scene_subheader="Partner Feedback")
)
cramped_room_options_scene_1 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="cramped_room_options_scene_1", experiment_config={})

counter_circuit_sp_0 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="counter_circuit_sp_0", experiment_config={})
    .pyodide(
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/counter_circuit_environment_initialization.py"
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play with a partner for a single round. "
        "This will be followed by a round with a different partner "
        "in the same environment layout."
        "<br><br> "
        "You will be playing on the layout pictured below. "
        '<center><img src="static/assets/overcooked/counter_circuit.png" alt="Annotated Overcooked environment." height="270" width="315"></center>'
        "When the button activates, click it to begin. "
        "</p></center>",
    )
    .rendering(
        game_width=overcooked_utils.TILE_SIZE * 9,
        game_height=overcooked_utils.TILE_SIZE * 7,
    )
)
counter_circuit_ibc_1 = (
    copy.deepcopy(counter_circuit_sp_0)
    .scene(scene_id="counter_circuit_ibc_1", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
)


counter_circuit_ibc_0 = (
    copy.deepcopy(counter_circuit_sp_0)
    .scene(scene_id="counter_circuit_ibc_0", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play another round on the same layout. "
        "After this round, you will provide your preference "
        "between the two partners you interacted with. "
        "When the button activates, click it to begin. "
        "</p></center>",
    )
)
counter_circuit_sp_1 = (
    copy.deepcopy(counter_circuit_ibc_0)
    .scene(scene_id="counter_circuit_sp_1", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING)
)


counter_circuit_options_scene_0 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="counter_circuit_options_scene_0", experiment_config={})
counter_circuit_options_scene_1 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="counter_circuit_options_scene_1", experiment_config={})


forced_coordination_sp_0 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="forced_coordination_sp_0", experiment_config={})
    .pyodide(
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/forced_coordination_environment_initialization.py"
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play with a partner for a single round. "
        "This will be followed by a round with a different partner "
        "in the same environment layout."
        "<br><br> "
        "You will be playing on the layout pictured below. "
        '<center><img src="static/assets/overcooked/forced_coordination.png" alt="Annotated Overcooked environment." height="270" width="315"></center>'
        "When the button activates, click it to begin. "
        "</p></center>",
    )
    .rendering(
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 7,
    )
)
forced_coordination_ibc_1 = (
    copy.deepcopy(forced_coordination_sp_0)
    .scene(scene_id="forced_coordination_ibc_1", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
)


forced_coordination_ibc_0 = (
    copy.deepcopy(forced_coordination_sp_0)
    .scene(scene_id="forced_coordination_ibc_0", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play another round on the same layout. "
        "After this round, you will provide your preference "
        "between the two partners you interacted with. "
        "When the button activates, click it to begin. "
        "</p></center>",
    )
)
forced_coordination_sp_1 = (
    copy.deepcopy(forced_coordination_ibc_0)
    .scene(scene_id="forced_coordination_sp_1", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING)
)

forced_coordination_options_scene_0 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="forced_coordination_options_scene_0", experiment_config={})
forced_coordination_options_scene_1 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="forced_coordination_options_scene_1", experiment_config={})

asymmetric_advantages_sp_0 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="asymmetric_advantages_sp_0", experiment_config={})
    .pyodide(
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/asymmetric_advantages_environment_initialization.py"
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play with a partner for a single round. "
        "This will be followed by a round with a different partner "
        "in the same environment layout."
        "<br><br> "
        "You will be playing on the layout pictured below. "
        '<center><img src="static/assets/overcooked/asymmetric_advantages.png" alt="Annotated Overcooked environment." height="270" width="315"></center>'
        "When the button activates, click it to begin. "
        "</p></center>",
    )
    .rendering(
        game_width=overcooked_utils.TILE_SIZE * 11,
        game_height=overcooked_utils.TILE_SIZE * 7,
    )
)
asymmetric_advantages_ibc_1 = (
    copy.deepcopy(asymmetric_advantages_sp_0)
    .scene(scene_id="asymmetric_advantages_ibc_1", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
)

asymmetric_advantages_ibc_0 = (
    copy.deepcopy(asymmetric_advantages_sp_0)
    .scene(scene_id="asymmetric_advantages_ibc_0", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play another round on the same layout. "
        "After this round, you will provide your preference "
        "between the two partners you interacted with. "
        "When the button activates, click it to begin. "
        "</p></center>",
    )
)
asymmetric_advantages_sp_1 = (
    copy.deepcopy(asymmetric_advantages_ibc_0)
    .scene(scene_id="asymmetric_advantages_sp_1", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING)
)

asymmetric_advantages_options_scene_0 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="asymmetric_advantages_options_scene_0", experiment_config={})

asymmetric_advantages_options_scene_1 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="asymmetric_advantages_options_scene_1", experiment_config={})

coordination_ring_sp_0 = (
    copy.deepcopy(cramped_room_sp_0)
    .scene(scene_id="coordination_ring_sp_0", experiment_config={})
    .pyodide(
        environment_initialization_code_filepath="interactive_gym/examples/cogrid_overcooked/pyodide_overcooked/env_initialization/coordination_ring_environment_initialization.py"
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play with a partner for a single round. "
        "This will be followed by a round with a different partner "
        "in the same environment layout."
        "<br><br> "
        "You will be playing on the layout pictured below. "
        '<center><img src="static/assets/overcooked/coordination_ring.png" alt="Annotated Overcooked environment." height="270" width="315"></center>'
        "When the button activates, click it to begin. "
        "</p></center>",
    )
    .rendering(
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 7,
    )
)

coordination_ring_ibc_1 = (
    copy.deepcopy(coordination_ring_sp_0)
    .scene(scene_id="coordination_ring_ibc_1", experiment_config={})
    .policies(policy_mapping=IBC_POLICY_MAPPING)
)

coordination_ring_ibc_0 = (
    copy.deepcopy(coordination_ring_sp_0)
    .policies(policy_mapping=IBC_POLICY_MAPPING)
    .scene(scene_id="coordination_ring_ibc_0", experiment_config={})
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "You'll now play another round on the same layout. "
        "After this round, you will provide your preference "
        "between the two partners you interacted with. "
        "When the button activates, click it to begin. "
        "</p></center>",
    )
)

coordination_ring_sp_1 = (
    copy.deepcopy(coordination_ring_ibc_0)
    .scene(scene_id="coordination_ring_sp_1", experiment_config={})
    .policies(policy_mapping=SP_POLICY_MAPPING)
)
coordination_ring_options_scene_0 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="coordination_ring_options_scene_0", experiment_config={})


coordination_ring_options_scene_1 = copy.deepcopy(
    cramped_room_options_scene_0
).scene(scene_id="coordination_ring_options_scene_1", experiment_config={})


cramped_room_0 = scene.SceneWrapper(
    scenes=[cramped_room_sp_0, cramped_room_ibc_0, cramped_room_options_scene_0]
)
cramped_room_1 = scene.SceneWrapper(
    scenes=[cramped_room_ibc_1, cramped_room_sp_1, cramped_room_options_scene_1]
)
counter_circuit_0 = scene.SceneWrapper(
    scenes=[
        counter_circuit_sp_0,
        counter_circuit_ibc_0,
        counter_circuit_options_scene_0,
    ]
)
counter_circuit_1 = scene.SceneWrapper(
    scenes=[
        counter_circuit_ibc_1,
        counter_circuit_sp_1,
        counter_circuit_options_scene_1,
    ]
)
forced_coordination_0 = scene.SceneWrapper(
    scenes=[
        forced_coordination_sp_0,
        forced_coordination_ibc_0,
        forced_coordination_options_scene_0,
    ]
)
forced_coordination_1 = scene.SceneWrapper(
    scenes=[
        forced_coordination_ibc_1,
        forced_coordination_sp_1,
        forced_coordination_options_scene_1,
    ]
)
asymmetric_advantages_0 = scene.SceneWrapper(
    scenes=[
        asymmetric_advantages_sp_0,
        asymmetric_advantages_ibc_0,
        asymmetric_advantages_options_scene_0,
    ]
)
asymmetric_advantages_1 = scene.SceneWrapper(
    scenes=[
        asymmetric_advantages_ibc_1,
        asymmetric_advantages_sp_1,
        asymmetric_advantages_options_scene_1,
    ]
)
coordination_ring_0 = scene.SceneWrapper(
    scenes=[
        coordination_ring_sp_0,
        coordination_ring_ibc_0,
        coordination_ring_options_scene_0,
    ]
)
coordination_ring_1 = scene.SceneWrapper(
    scenes=[
        coordination_ring_ibc_1,
        coordination_ring_sp_1,
        coordination_ring_options_scene_1,
    ]
)


feedback_scene = static_scene.TextBoxOnly(
    text_box_header="If desired, please provide any additional feedback on your experience with this game. You will receive a completion code on the next page.",
    required=False,
).scene(
    scene_id="feedback_scene",
)


end_scene = (
    static_scene.CompletionCodeScene()
    .scene(
        scene_id="end_completion_code_scene",
        should_export_metadata=True,
        experiment_config={},
    )
    .display(
        scene_header="Thank you for participating!",
    )
    # .redirect(url="https://www.google.com")
)
