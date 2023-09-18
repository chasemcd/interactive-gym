import gymnasium as gym

import interactive_server
import remote_config


def env_creator(render_mode: str = "rgb_array", *args, **kwargs):
    return gym.make("LunarLander-v2", render_mode=render_mode)


action_mapping = {"left": 1, "right": 3, "up": 2}
config = (
    remote_config.RemoteConfig()
    .environment(env_creator=env_creator, env_name="LunarLander-v2")
    .gameplay(human_id="agent-0", default_action=0, action_mapping=action_mapping)
    .user_experience(fps=20)
)


if __name__ == "__main__":
    interactive_server.run(config)
