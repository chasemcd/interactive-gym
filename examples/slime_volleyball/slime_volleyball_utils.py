import math

import gymnasium as gym
import numpy as np
from configurations import object_contexts
from examples.slime_volleyball.slime_volleyball import slimevolley_env
from examples.slime_volleyball.slime_volleyball.core import constants
from configurations import remote_config


Y_OFFSET = 0.018


def to_x(x):
    return x / constants.REF_W + 0.5


def to_y(y):
    return 1 - y / constants.REF_W


def slime_volleyball_env_to_rendering(
    env: slimevolley_env.SlimeVolleyEnv, config: remote_config.RemoteConfig
) -> list:
    render_objects = []

    fence = object_contexts.Line(
        uuid="fence",
        color="#000000",
        points=[
            (
                to_x(env.game.fence.x),
                to_y(env.game.fence.y + env.game.fence.h / 2),
            ),
            (
                to_x(env.game.fence.x),
                to_y(env.game.fence.y - env.game.fence.h / 2),
            ),
        ],
        width=env.game.fence.w * config.game_width / constants.REF_W,
    )
    render_objects.append(fence)

    fence_stub = object_contexts.Circle(
        uuid="fence_stub",
        color="#000000",
        x=to_x(env.game.fence_stub.x),
        y=to_y(env.game.fence_stub.y),
        radius=env.game.fence_stub.r * config.game_width / constants.REF_W,
    )
    render_objects.append(fence_stub)

    render_objects += generate_slime_agent_objects(
        "agent_left",
        x=env.game.agent_left.x,
        y=env.game.agent_left.y,
        dir=env.game.agent_left.dir,
        radius=env.game.agent_left.r,
        color="#FF0000",
        config=config,
        env=env,
    )

    render_objects += generate_slime_agent_objects(
        "agent_right",
        x=env.game.agent_right.x,
        y=env.game.agent_right.y,
        dir=env.game.agent_right.dir,
        radius=env.game.agent_right.r,
        color="#0000FF",
        config=config,
        env=env,
    )

    ball = object_contexts.Circle(
        uuid="ball",
        color="#000000",
        x=env.game.ball.x / constants.REF_W + 0.5,
        y=1 - env.game.ball.y / constants.REF_W,
        radius=env.game.ball.r * config.game_width / constants.REF_W,
    )
    render_objects.append(ball)

    ground = object_contexts.Line(
        uuid="ground",
        color="#747275",
        points=[
            (
                0,
                1
                - env.game.ground.y / constants.REF_W
                - constants.REF_U / constants.REF_W / 2,
            ),
            (
                1,
                1
                - env.game.ground.y / constants.REF_W
                - constants.REF_U / constants.REF_W / 2,
            ),
        ],
        fill_below=True,
        width=env.game.ground.w / constants.REF_W,
        depth=-1,
    )
    render_objects.append(ground)

    border = object_contexts.Polygon(
        uuid="border",
        color="#AEF359",
        points=[(0, 0), (1, 0), (1, 1), (0, 1)],
        depth=-5,
        alpha=0.1,
    )
    render_objects.append(border)

    return [obj.as_dict() for obj in render_objects]


def generate_slime_agent_objects(
    identifier: str,
    x: int,
    y: int,
    dir: int,
    radius: int,
    color: str,
    env: slimevolley_env.SlimeVolleyEnv,
    config: remote_config.RemoteConfig,
    resolution: int = 30,
):
    objects = []
    points = []
    for i in range(resolution + 1):
        ang = math.pi - math.pi * i / resolution
        points.append(
            (to_x(math.cos(ang) * radius + x), to_y(math.sin(ang) * radius + y))
        )

    objects.append(
        object_contexts.Polygon(
            uuid=f"{identifier}_body", color=color, points=points, depth=-1
        )
    )

    # Eyes that track the ball!
    angle = math.pi * 60 / 180
    if dir == 1:
        angle = math.pi * 120 / 180

    c = math.cos(angle)
    s = math.sin(angle)
    ballX = env.game.ball.x - (x + (0.6) * radius * c)
    ballY = env.game.ball.y - (y + (0.6) * radius * s)
    dist = math.sqrt(ballX * ballX + ballY * ballY)
    eyeX = ballX / dist
    eyeY = ballY / dist

    pupil = object_contexts.Circle(
        uuid=f"{identifier}_eye_pupil",
        x=to_x(x + (0.6) * radius * c + eyeX * 0.15 * radius),
        y=to_y(y + (0.6) * radius * s + eyeY * 0.15 * radius),
        color="#000000",
        radius=radius * 2,
        depth=2,
    )

    eye_white = object_contexts.Circle(
        uuid=f"{identifier}_eye_white",
        x=to_x(x + (0.6) * radius * c),
        y=to_y(y + (0.6) * radius * s),
        color="#FFFFFF",
        radius=radius * 4,
        depth=1,
    )

    objects.extend([eye_white, pupil])

    return objects
