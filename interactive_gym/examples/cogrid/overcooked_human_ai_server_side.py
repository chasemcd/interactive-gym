from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from cogrid.envs import registry

from interactive_gym.configurations import (
    configuration_constants,
)
from interactive_gym.examples.cogrid import (
    overcooked_utils,
)
from interactive_gym.scenes import static_scene
from interactive_gym.scenes import gym_scene
from interactive_gym.scenes import stager

from interactive_gym.server import app
from interactive_gym.scenes import stager

from interactive_gym.configurations import experiment_config

MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


POLICY_MAPPING = {
    0: configuration_constants.PolicyTypes.Human,
    1: "interactive_gym/examples/cogrid/policies/ibc_0.onnx",
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    return registry.make("Overcooked-CrampedRoom-V0", render_mode=None)


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "q": Toggle,
}

start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="overcooked_start_scene",
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body_filepath="interactive_gym/server/static/templates/overcooked_instructions.html",
    )
)

overcooked_gym_scene = (
    gym_scene.GymScene()
    .scene(scene_id="cramped_room_sp_0", experiment_config={})
    .policies(policy_mapping=POLICY_MAPPING, frame_skip=5)
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
)

end_scene = static_scene.EndScene().display(
    scene_header="Thank you for participating!",
)


stager = stager.Stager(
    scenes=[
        start_scene,
        overcooked_gym_scene,
        end_scene,
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
        .experiment(stager=stager, experiment_id="overcooked_server_test")
        .hosting(port=5702, host="0.0.0.0")
    )

    app.run(experiment_config)
