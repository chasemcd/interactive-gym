import gymnasium

import gymnasium as gym
from gymnasium.envs.classic_control import mountain_car
import numpy as np
from utils import object_contexts


def mountaincar_to_render_state(env: gym.Env) -> list[dict]:

    min_pos, max_pos = env.unwrapped.min_position, env.unwrapped.max_position
    env_ = env.unwrapped

    def _normalize_x(vals, minn=min_pos, maxx=max_pos):
        vals -= minn
        return vals / (maxx - minn)

    # Get coordinates of the car
    car_x = env_.state[0]
    car_y = 1 - env_._height(car_x)
    car_x = _normalize_x(car_x)
    car_sprite = object_contexts.Sprite(
        uuid="car", image_name="green_ball.png", x=car_x, y=car_y
    )

    # Get coordinates of the flag
    flagx = env_.goal_position
    flagy1 = 1 - env_._height(env_.goal_position)
    flagy2 = 0.05
    flagx = _normalize_x(flagx)
    flag = object_contexts.Line(
        uuid="flag_line",
        color="#00FF00",
        points=[(flagx, flagy1), (flagx, flagy2)],
        width=5,
    )

    # # Get line coordinates
    xs = np.linspace(min_pos, max_pos, 100)
    ys = 1 - env_._height(xs)
    xs = _normalize_x(xs)
    xys = list(zip((xs), ys))
    line = object_contexts.Line(
        uuid="ground_line", color="#964B00", points=xys, width=1, fill_below=True
    )

    return [car_sprite.as_dict(), line.as_dict(), flag.as_dict()]


if __name__ == "__main__":
    env = gym.make("MountainCar-v0").unwrapped
    obs, _ = env.reset()
    a = "b"
