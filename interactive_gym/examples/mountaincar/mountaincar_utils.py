from __future__ import annotations

import os

import gymnasium as gym
import numpy as np

from interactive_gym.configurations import object_contexts

ball_rotation = 0
prev_x = None
FPS = 30

ASSET_PATH = "static/assets/"


def overcooked_preload_assets_spec() -> (
    list[
        object_contexts.AtlasSpec
        | object_contexts.MultiAtlasSpec
        | object_contexts.ImgSpec
    ]
):
    return [
        object_contexts.ImgSpec(
            "green_ball", img_path=os.path.join(ASSET_PATH, "green_ball.png")
        ).as_dict()
    ]


def mountaincar_to_render_state(env: gym.Env, *args, **kwargs) -> list[dict]:
    global ball_rotation, prev_x
    y_offset = 0.05
    min_pos, max_pos = env.unwrapped.min_position, env.unwrapped.max_position
    env_ = env.unwrapped

    def _normalize_x(vals, minn=min_pos, maxx=max_pos):
        vals -= minn
        return vals / (maxx - minn)

    # Get coordinates of the car
    car_x = env_.state[0]
    if prev_x is None:
        prev_x = car_x

    car_y = 1 - env_._height(car_x) + y_offset
    car_x = _normalize_x(car_x)

    ball_rotation += (car_x - prev_x) * 2000
    prev_x = car_x

    car_sprite = object_contexts.Sprite(
        uuid="car",
        image_name="green_ball",
        x=car_x,
        y=car_y,
        height=16,
        width=16,
        angle=ball_rotation,
    )

    # Get coordinates of the flag
    flagx = env_.goal_position
    flagy1 = 1 - env_._height(env_.goal_position)
    flagy2 = 0.05
    flagx = _normalize_x(flagx)
    flag_pole = object_contexts.Line(
        uuid="flag_line",
        color="#000000",
        points=[(flagx, flagy1), (flagx, flagy2)],
        width=3,
    )

    flag = object_contexts.Polygon(
        uuid="flag",
        color="#00FF00",
        points=[
            (flagx, flagy1),
            (flagx, flagy1 + 0.03),
            (flagx - 0.02, flagy1 + 0.015),
        ],
    )

    # Get line coordinates
    xs = np.linspace(min_pos, max_pos, 100)
    ys = 1 - env_._height(xs) + y_offset
    xs = _normalize_x(xs)
    xys = list(zip((xs), ys))
    line = object_contexts.Line(
        uuid="ground_line", color="#964B00", points=xys, width=1, fill_below=True
    )

    seconds_left = (env._max_episode_steps - env._elapsed_steps) / FPS
    time = object_contexts.Text(
        uuid="time_left",
        text=f"{np.round(seconds_left, 1):.1f}s remaining",
        x=0.05,
        y=0.05,
        size=12,
    )

    return [
        car_sprite.as_dict(),
        line.as_dict(),
        flag_pole.as_dict(),
        flag.as_dict(),
        time.as_dict(),
    ]
