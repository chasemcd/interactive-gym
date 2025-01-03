import slime_volleyball.slimevolley_env as slimevolley_env
from slime_volleyball.core import constants
import math
import typing

import dataclasses


Y_OFFSET = 0.018


def to_x(x):
    return x / constants.REF_W + 0.5


def to_y(y):
    return 1 - y / constants.REF_W


@dataclasses.dataclass
class Line:
    """
    Context for a line object to render it.

    :param uuid: Unique identifier for the line
    :type uuid: str
    :param color: Color of the line
    :type color: str
    :param width: Width of the line
    :type width: int
    :param points: List of points defining the line
    :type points: list[tuple[float, float]]

    .. testcode::

        line = Line(
            uuid="line1",
            color="#FF0000",
            width=2,
            points=[(0, 0), (100, 100), (200, 0)],
            fill_below=True,
            depth=1
        )

    """

    uuid: str
    color: str
    width: int
    points: list[tuple[float, float]]
    object_type: str = "line"
    fill_below: bool = False
    fill_above: bool = False
    depth: int = -1
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Circle:
    """
    Context for a circle object to render it.

    :param uuid: Unique identifier for the circle
    :type uuid: str
    :param color: Color of the circle
    :type color: str
    :param x: X-coordinate of the circle's center
    :type x: float
    :param y: Y-coordinate of the circle's center
    :type y: float
    :param radius: Radius of the circle
    :type radius: int
    :param alpha: Alpha value for the circle's transparency
    :type alpha: float
    :param object_type: Type of the object
    :type object_type: str
    :param depth: Rendering depth of the circle. Higher values are rendered on top
    :type depth: int
    :param permanent: Whether the circle should persist across steps.

    .. testcode::

        circle = Circle(
            uuid="circle1",
            color="#00FF00",
            x=150.0,
            y=150.0,
            radius=50,
            alpha=0.8,
            depth=2,
            permanent=True
        )
    """

    uuid: str
    color: str
    x: float
    y: float
    radius: int
    alpha: float = 1
    object_type: str = "circle"
    depth: int = -1
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Polygon:
    """
    Context for a polygon object to render it.

    :param uuid: Unique identifier for the polygon
    :type uuid: str
    :param color: Color of the polygon
    :type color: str
    :param points: List of points defining the polygon
    :type points: list[tuple[float, float]]
    :param alpha: Alpha value for the polygon's transparency
    :type alpha: float
    :param object_type: Type of the object
    :type object_type: str
    :param depth: Rendering depth of the polygon. Higher values are rendered on top
    :type depth: int
    :param permanent: Whether the polygon should persist across steps.
    :type permanent: bool

    .. testcode::

        polygon = Polygon(
            uuid="polygon1",
            color="#0000FF",
            points=[(0, 0), (100, 0), (100, 100), (0, 100)],
            alpha=0.5,
            depth=3,
            permanent=False
        )

    """

    uuid: str
    color: str
    points: list[tuple[float, float]]
    alpha: float = 1
    object_type: str = "polygon"
    depth: int = -1
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def slime_volleyball_env_to_rendering(
    env: slimevolley_env.SlimeVolleyEnv,
) -> list:
    render_objects = []

    # static objects only rendered on the first frame
    if env.t == 0:
        fence = Line(
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
            width=env.game.fence.w * 600 / constants.REF_W,
            permanent=True,
        )
        render_objects.append(fence)

        fence_stub = Circle(
            uuid="fence_stub",
            color="#000000",
            x=to_x(env.game.fence_stub.x),
            y=to_y(env.game.fence_stub.y),
            radius=env.game.fence_stub.r * 600 / constants.REF_W,
            permanent=True,
        )
        render_objects.append(fence_stub)

        ground = Line(
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
            permanent=True,
        )
        render_objects.append(ground)

    render_objects += generate_slime_agent_objects(
        "agent_left",
        x=env.game.agent_left.x,
        y=env.game.agent_left.y,
        dir=env.game.agent_left.dir,
        radius=env.game.agent_left.r,
        is_boosting=False,
        color="#FF0000",
        env=env,
    )

    render_objects += generate_slime_agent_objects(
        "agent_right",
        x=env.game.agent_right.x,
        y=env.game.agent_right.y,
        dir=env.game.agent_right.dir,
        radius=env.game.agent_right.r,
        is_boosting=False,
        color="#0000FF",
        env=env,
    )

    terminateds, _ = env.get_terminateds_truncateds()
    ball = Circle(
        uuid="ball",
        color="#000000" if not terminateds["__all__"] else "#AAFF00",
        x=env.game.ball.x / constants.REF_W + 0.5,
        y=1 - env.game.ball.y / constants.REF_W,
        radius=env.game.ball.r * 600 / constants.REF_W,
    )
    render_objects.append(ball)

    return [obj.as_dict() for obj in render_objects]


def generate_slime_agent_objects(
    identifier: str,
    x: int,
    y: int,
    dir: int,
    radius: int,
    is_boosting: bool,
    color: str,
    env: slimevolley_env.SlimeVolleyEnv,
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
        Polygon(uuid=f"{identifier}_body", color=color, points=points, depth=-1)
    )

    if is_boosting:
        objects.append(
            Polygon(
                uuid=f"{identifier}_body_boost",
                color="#FFFF00",
                points=[p * 1.1 for p in points],
                depth=-1,
            )
        )
    # objects.append(
    #     Sprite(
    #         uuid=f"{identifier}_body_sprite",
    #         image_name="slime_blue.png" if "right" in identifier else "slime_red.png",
    #         x=to_x(x - radius),
    #         y=to_y(y) - 30 / config.game_height,
    #         height=30,
    #         width=36,
    #         depth=0,
    #     )
    # )

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

    pupil = Circle(
        uuid=f"{identifier}_eye_pupil",
        x=to_x(x + (0.6) * radius * c + eyeX * 0.15 * radius),
        y=to_y(y + (0.6) * radius * s + eyeY * 0.15 * radius),
        color="#000000",
        radius=radius * 2,
        depth=2,
    )

    eye_white = Circle(
        uuid=f"{identifier}_eye_white",
        x=to_x(x + (0.6) * radius * c),
        y=to_y(y + (0.6) * radius * s),
        color="#FFFFFF",
        radius=radius * 4,
        depth=1,
    )

    objects.extend([eye_white, pupil])

    return objects


class SlimeVBEnvIG(slimevolley_env.SlimeVolleyEnv):
    def render(self):
        assert self.render_mode == "interactive-gym"
        return slime_volleyball_env_to_rendering(self)

    # def reset(self):
    #     obs, infos = super().reset()
    #     obs = {k: v["obs"] for k, v in obs.items()}
    #     return obs, infos

    # def step(self, actions):
    #     obs, rews, terminateds, truncateds, infos = super().step(actions)
    #     obs = {k: v["obs"] for k, v in obs.items()}
    #     return obs, rews, terminateds, truncateds, infos


env = SlimeVBEnvIG(config={"human_inputs": True}, render_mode="interactive-gym")
