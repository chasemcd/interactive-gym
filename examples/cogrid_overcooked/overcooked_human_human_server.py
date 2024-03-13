import eventlet

eventlet.monkey_patch()

import argparse
from cogrid.envs import registry

from configurations import remote_config
from server import server_app
from configurations import configuration_constants
from examples.cogrid_overcooked import overcooked_utils
from examples.cogrid_overcooked import overcooked_callback


MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


POLICY_MAPPING = {
    "agent-0": configuration_constants.PolicyTypes.Human,
    "agent-1": configuration_constants.PolicyTypes.Human,
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


config = (
    remote_config.RemoteConfig()
    .policies(policy_mapping=POLICY_MAPPING)
    .environment(env_creator=env_creator, env_name="cogrid_overcooked")
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
        num_episodes=20,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
        callback=overcooked_callback.OvercookedCallback(),
    )
    .hosting(host="0.0.0.0", max_concurrent_games=100, max_ping=100)
    .user_experience(
        page_title="Overcooked",
        instructions_html_file="server/static/templates/overcooked_instructions.html",
        welcome_header_text="Overcooked",
        game_header_text="Overcooked",
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
        waitroom_time_randomization_interval_s=(
            5,
            25,
        ),  # fake waitroom of 5 to 25 seconds
        final_page_header_text="Overcooked",
        final_page_text="Thanks for playing, you will be redirected shortly...",
        end_game_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_agZ3V7Uj4jfVweG",
        waitroom_timeout=10_000,  # 5 * 60_000,  # 2 minutes in waitroom
        waitroom_timeout_redirect_url="https://cmu.ca1.qualtrics.com/jfe/form/SV_bIskl3fFOPC6ayy",
    )
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5701, help="Port number to listen on"
    )
    args = parser.parse_args()

    config.hosting(port=args.port)

    server_app.run(config)
