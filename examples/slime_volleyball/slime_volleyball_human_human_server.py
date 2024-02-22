from slime_volleyball import slimevolley_env

from configurations import remote_config
from server import server_app
from server.remote_game import PolicyTypes
from examples.slime_volleyball import slime_volleyball_utils

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
    "agent_left": PolicyTypes.Human,
    "agent_right": PolicyTypes.Human,
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    config = {
        "human_inputs": POLICY_MAPPING.get("agent_left") == PolicyTypes.Human,
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
    .policies(policy_mapping=POLICY_MAPPING)
    .environment(env_creator=env_creator, env_name="slime_volleyball")
    .rendering(
        fps=30,
        env_to_state_fn=slime_volleyball_utils.slime_volleyball_env_to_rendering,
        hud_text_fn=slime_volleyball_utils.hud_text_fn,
        game_width=600,
        game_height=400,
    )
    .gameplay(
        default_action=NOOP,
        action_mapping=action_mapping,
        num_episodes=10,
    )
    .hosting(port=5704, host="0.0.0.0", max_concurrent_games=10)
    .user_experience(
        page_title="Slime Volleyball",
        welcome_header_text="Slime Volleyball",
        instructions_html_file="server/static/templates/slime_volleyball_instructions.html",
        game_header_text="Slime Volleyball",
        game_page_text="Use the arrow keys to move your character!",
        final_page_header_text="Slime Volleyball",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        redirect_url="https://www.google.com/",
        redirect_timeout=240_000,
        waitroom_timeout=120_000,  # 2 minutes in waitroom
    )
)


if __name__ == "__main__":
    server_app.run(config)
