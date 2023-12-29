import gymnasium as gym

import interactive_server
import remote_config
from examples.mountaincar import mountaincar_utils

from gymnasium.envs import classic_control

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


def env_creator(render_mode: str = "rgb_array", *args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    return gym.make("MountainCar-v0", render_mode=render_mode)


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {"ArrowLeft": LEFT_ACCELERATION, "ArrowRight": RIGHT_ACCELERATION}

config = (
    remote_config.RemoteConfig()
    .environment(env_creator=env_creator, env_name="MountainCar-v0")
    .rendering(fps=20, env_to_state_fn=mountaincar_utils.mountaincar_to_render_state)
    .gameplay(
        human_id="agent-0", default_action=NOOP_ACTION, action_mapping=action_mapping,
    )
    .hosting(port=8000)
    .user_experience(
        start_header_text="Interactive MountainCar-v0",
        start_page_text="This is an interactive adaptation of the MountainCar-v0 environment. "
        "Use the left and right arrow keys to move the ball left and right."
        "The goal is to get the ball to the green flag before time runs out.",
    )
)


if __name__ == "__main__":
    interactive_server.run(config)
