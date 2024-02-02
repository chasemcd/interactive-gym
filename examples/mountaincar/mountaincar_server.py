import gymnasium as gym

from configurations import remote_config
from examples.mountaincar import mountaincar_utils
from server import server_app
from server.remote_game import PolicyTypes

"""
This is an example script for running MountainCar-v0 in
a local server. Simply run the script and navigate
to http://127.0.0.1:8000 in your browser. 

MountainCar-v0 has three actions: do nothing, accelerate left
and accelerate right. We set "do nothing" to be the default
for when there is no key pressed. Accelerating left and right
are the left and right arrow keys, respectively.  
"""

LEFT_ACCELERATION = 0
NOOP_ACTION = 1
RIGHT_ACCELERATION = 2


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    return gym.make("MountainCar-v0", render_mode="rgb_array")


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {"ArrowLeft": LEFT_ACCELERATION, "ArrowRight": RIGHT_ACCELERATION}

config = (
    remote_config.RemoteConfig()
    .policies(policy_mapping={PolicyTypes.Human: PolicyTypes.Human})
    .environment(env_creator=env_creator, env_name="MountainCar-v0")
    .rendering(fps=30, env_to_state_fn=mountaincar_utils.mountaincar_to_render_state)
    .gameplay(
        human_id="agent-0",
        default_action=NOOP_ACTION,
        action_mapping=action_mapping,
        num_episodes=2,
    )
    .hosting(port=5703, host="0.0.0.0")
    .user_experience(
        page_title="Interactive MountainCar-v0",
        welcome_header_text="Interactive MountainCar-v0",
        welcome_text="This is an interactive adaptation of the MountainCar-v0 environment. "
        "Use the left and right arrow keys to move the ball left and right."
        "The goal is to get the ball to the flag before time runs out.",
        game_header_text="Interactive MountainCar-v0",
        game_page_text="Use the left and right arrows to move the ball up the hill!",
        final_page_header_text="Interactive MountainCar-v0",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        redirect_url="https://www.cmu.edu/dietrich/sds/ddmlab",
        redirect_timeout=20_000,
        waitroom_timeout=120_000,  # 2 minutes in waitroom
    )
)


if __name__ == "__main__":
    server_app.run(config)
