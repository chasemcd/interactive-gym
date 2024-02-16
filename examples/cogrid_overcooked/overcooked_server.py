from cogrid.envs import registry

from configurations import remote_config
from server import server_app
from server.remote_game import PolicyTypes
from configurations import configuration_constants
from examples.cogrid_overcooked import overcooked_utils

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
    "agent-0": PolicyTypes.Human,
    # "agent_right": PolicyTypes.Human,
}


def env_creator(*args, **kwargs):
    """Generic function to return the Gymnasium environment"""
    config = {
        "human_inputs": POLICY_MAPPING.get("agent_left") == PolicyTypes.Human,
    }
    return registry.make("SAOvercooked-V0", render_mode="rgb_array")


# Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
action_mapping = {
    "ArrowLeft": MoveLeft,
    "ArrowRight": MoveRight,
    "ArrowUp": MoveUp,
    "ArrowDown": MoveDown,
    "w": PickupDrop,
    "q": Toggle,
}


config = (
    remote_config.RemoteConfig()
    .policies(policy_mapping=POLICY_MAPPING)
    .environment(env_creator=env_creator, env_name="slime_volleyball")
    .rendering(
        fps=10,
        # env_to_state_fn=overcooked_utils.overcooked_env_to_render_fn,
        game_width=600,
        game_height=400,
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=2,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .hosting(port=5703, host="0.0.0.0")
    .user_experience(
        page_title="Single Agent Overcooked",
        welcome_header_text="Overcooked",
        welcome_text="In this game, you'll attempt to deliver as many cooked dishes as possible. You'll pick up onions (in the pile on the left), drop three of them in the grey pot (top), pick up a bowl (right stack), and pick up the soup to put into the bowl when it's done cooking. You'll score one point for each soup you deliver to the green delivery area.",
        game_header_text="Overcooked",
        game_page_text="Use the arrow keys to move, w to pick up and drop, and q to deliver dishes to the green delivery area! ",
        final_page_header_text="Overcooked",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        redirect_url="https://www.google.com/",
        redirect_timeout=240_000,
        waitroom_timeout=120_000,  # 2 minutes in waitroom
    )
)


if __name__ == "__main__":
    server_app.run(config)
