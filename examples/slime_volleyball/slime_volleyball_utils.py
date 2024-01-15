import gymnasium as gym
import numpy as np
from configurations import object_contexts
from examples.slime_volleyball.slime_volleyball import slimevolley_env


def slime_volleyball_env_to_rendering(env: slimevolley_env.SlimeVolleyEnv) -> list:
    render_objects = []

    fence = object_contexts.Line(
        uuid="fence",
        color="#000000",
        points=[
            (env.game.fence.x / 48 + 0.5, 1 - env.game.fence.y / 48),
            (
                env.game.fence.x / 48 + 0.5,
                1 - (env.game.fence.y - env.game.fence.h) / 48,
            ),
        ],
        width=15,
    )
    render_objects.append(fence)

    left_agent = object_contexts.Circle(
        uuid="agent_left",
        color="#FF0000",
        x=env.game.agent_left.x / 48 + 0.5,
        y=1 - env.game.agent_left.y / 48,
        radius=env.game.agent_left.r * 9,
    )
    render_objects.append(left_agent)

    right_agent = object_contexts.Circle(
        uuid="agent_right",
        color="#0000FF",
        x=env.game.agent_right.x / 48 + 0.5,
        y=1 - env.game.agent_right.y / 48,
        radius=env.game.agent_right.r * 9,
    )
    render_objects.append(right_agent)

    ball = object_contexts.Circle(
        uuid="ball",
        color="#000000",
        x=env.game.ball.x / 48 + 0.5,
        y=1 - env.game.ball.y / 48,
        radius=env.game.ball.r * 15,
    )
    render_objects.append(ball)

    ground = object_contexts.Line(
        uuid="ground",
        color="#747275",
        points=[(0, 1 - env.game.ground.y / 48), (1, 1 - env.game.ground.y / 48)],
        fill_below=True,
        width=5,
        depth=1,
    )
    render_objects.append(ground)

    return [obj.as_dict() for obj in render_objects]
