import gymnasium as gym

import interactive_server
import remote_config


def env_creator(render_mode: str = "rgb_array", *args, **kwargs):
    return gym.make("MountainCar-v0", render_mode=render_mode)


action_mapping = {"ArrowLeft": 0, "ArrowRight": 2}

config = (
    remote_config.RemoteConfig()
    .environment(env_creator=env_creator, env_name="MountainCar-v0")
    .gameplay(human_id="agent-0", default_action=1, action_mapping=action_mapping)
    .user_experience(fps=10)
)


if __name__ == "__main__":
    interactive_server.run(config)
