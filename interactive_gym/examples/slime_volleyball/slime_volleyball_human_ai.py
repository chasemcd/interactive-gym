import eventlet

eventlet.monkey_patch()

from slime_volleyball import slimevolley_env

from interactive_gym.configurations import remote_config
from interactive_gym.configurations import configuration_constants
from interactive_gym.server import server_app
from interactive_gym.examples.slime_volleyball import slime_volleyball_utils
from interactive_gym.examples.slime_volleyball import slime_volleyball_callback
from interactive_gym.utils import onnx_inference_utils

"""
This is an example script for running MountainCar-v0 in
a local server. Simply run the script and navigate
to http://127.0.0.1:8000 in your browser. 

MountainCar-v0 has three actions: do nothing, accelerate left
and accelerate right. We set "do nothing" to be the default
for when there is no key pressed. Accelerating left and right
are the left and right arrow keys, respectively.  
"""

NOOP = 0
LEFT = 1
UPLEFT = 2
UP = 3
UPRIGHT = 4
RIGHT = 5


POLICY_MAPPING = {
    "agent_left": configuration_constants.PolicyTypes.Human,
    "agent_right": "examples/slime_volleyball/policies/model.onnx",
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    config = {
        "human_inputs": POLICY_MAPPING.get("agent_left")
        == configuration_constants.PolicyTypes.Human,
    }
    return slimevolley_env.SlimeVolleyEnv(config=config)


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": LEFT,
    ("ArrowLeft", "ArrowUp"): UPLEFT,
    "ArrowUp": UP,
    ("ArrowRight", "ArrowUp"): UPRIGHT,
    "ArrowRight": RIGHT,
}


config = (
    remote_config.RemoteConfig()
    .policies(
        policy_mapping=POLICY_MAPPING,
        policy_inference_fn=onnx_inference_utils.onnx_model_inference_fn,
        load_policy_fn=onnx_inference_utils.load_onnx_policy_fn,
        frame_skip=1,
    )
    .environment(env_creator=env_creator, env_name="slime_volleyball")
    .rendering(
        fps=35,
        env_to_state_fn=slime_volleyball_utils.slime_volleyball_env_to_rendering,
        assets_to_preload=slime_volleyball_utils.slime_volleyball_preload_assets_spec(),
        hud_text_fn=slime_volleyball_utils.hud_text_fn,
        game_width=600,
        game_height=400,
        background="#B9EBFF",
    )
    .gameplay(
        default_action=NOOP,
        action_population_method=configuration_constants.ActionSettings.PreviousSubmittedAction,
        action_mapping=action_mapping,
        num_episodes=50,
        callback=slime_volleyball_callback.SlimeVolleyballCallback(),
    )
    .hosting(port=5705, host="0.0.0.0", max_concurrent_games=100, max_ping=100)
    .user_experience(
        page_title="Slime Volleyball",
        welcome_header_text="Slime Volleyball",
        instructions_html_file="server/static/templates/slime_volleyball_instructions.html",
        game_header_text="Slime Volleyball",
        game_page_html_fn=slime_volleyball_utils.slime_volleyball_game_page_header_fn,
        final_page_header_text="Slime Volleyball",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        end_game_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_b7yGut4znAui0hE",
        waitroom_timeout=5 * 60_000,  # 2 minutes in waitroom
        waitroom_timeout_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_bIskl3fFOPC6ayy",
    )
)


if __name__ == "__main__":
    server_app.run(config)
