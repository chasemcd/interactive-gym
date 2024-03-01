from cogrid.envs import registry

from configurations import remote_config
from server import server_app
from configurations import configuration_constants
from examples.cogrid_overcooked import overcooked_utils
from examples.cogrid_overcooked import overcooked_callback
from utils import onnx_inference_utils

"""
This is an example script for running MountainCar-v0 in
a local server. Simply run the script and navigate
to http://127.0.0.1:8000 in your browser. 

MountainCar-v0 has three actions: do nothing, accelerate left
and accelerate right. We set "do nothing" to be the default
for when there is no key pressed. Accelerating left and right
are the left and right arrow keys, respectively.  
"""

MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


POLICY_MAPPING = {
    "agent-0": configuration_constants.PolicyTypes.Human,
    "agent-1": "examples/cogrid_overcooked/policies/model.onnx",
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    return registry.make("Overcooked-V0", render_mode="rgb_array")


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "q": Toggle,
}


def dummy_query_fn(*args, **kwargs):
    return 6


def dummy_load_fn(bot, *args, **kwargs):
    return bot


config = (
    remote_config.RemoteConfig()
    .policies(
        policy_mapping=POLICY_MAPPING,
        policy_inference_fn=onnx_inference_utils.onnx_model_inference_fn,
        load_policy_fn=onnx_inference_utils.load_onnx_policy_fn,
        frame_skip=5,
    )
    .environment(env_creator=env_creator, env_name="cogrid_overcooked")
    .rendering(
        fps=30,
        env_to_state_fn=overcooked_utils.overcooked_env_to_render_fn,
        assets_to_preload=overcooked_utils.overcooked_preload_assets_spec(),
        hud_text_fn=overcooked_utils.hud_text_fn,
        game_width=overcooked_utils.TILE_SIZE * 9,
        game_height=overcooked_utils.TILE_SIZE * 10,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=20,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
        callback=overcooked_callback.OvercookedCallback(),
    )
    .hosting(port=5703, host="0.0.0.0", max_concurrent_games=100, max_ping=150)
    .user_experience(
        page_title="Overcooked",
        instructions_html_file="server/static/templates/overcooked_instructions.html",
        waitroom_time_randomization_interval_s=(
            5,
            25,
        ),  # fake waitroom of 5 to 25 seconds
        welcome_header_text="Overcooked",
        game_header_text="Overcooked",
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
        final_page_header_text="Overcooked",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        end_game_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_agZ3V7Uj4jfVweG",
        waitroom_timeout=5 * 60_000,  # 5 minutes in waitroom
        waitroom_timeout_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_bIskl3fFOPC6ayy",
    )
)


if __name__ == "__main__":
    server_app.run(config)
