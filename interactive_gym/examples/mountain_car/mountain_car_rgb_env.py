""""
MountainCar renders an environment using libraries that aren't
pure python. Here, we override the rgb_array rendering to 
use pure python in a way that will allow it to be run via Pyodide.

"""

from typing import Any
import numpy as np
from gymnasium.envs.classic_control.mountain_car import MountainCarEnv
import dataclasses


@dataclasses.dataclass
class RenderedEnvRGB:
    name: str
    game_image: list[list[float]]
    object_type: str = "rendered_env_rgb"

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


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

    def as_dict(self) -> dict[str, Any]:
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

    def as_dict(self) -> dict[str, Any]:
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

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class MountainCarRGBEnv(MountainCarEnv):

    def render(self):
        assert self.render_mode == "interactive-gym"

        y_offset = 0.05
        min_pos, max_pos = (
            env.unwrapped.min_position,
            env.unwrapped.max_position,
        )
        env_ = self.unwrapped

        def _normalize_x(vals, minn=min_pos, maxx=max_pos):
            vals -= minn
            return vals / (maxx - minn)

        # Get coordinates of the car
        car_x = env_.state[0]

        car_y = 1 - env_._height(car_x) + y_offset
        car_x = _normalize_x(car_x)

        car_sprite = Circle(
            uuid="car",
            color="#000000",
            x=car_x,
            y=car_y,
            radius=16,
        )

        # Get coordinates of the flag
        flagx = env_.goal_position
        flagy1 = 1 - env_._height(env_.goal_position)
        flagy2 = 0.05
        flagx = _normalize_x(flagx)
        flag_pole = Line(
            uuid="flag_line",
            color="#000000",
            points=[(flagx, flagy1), (flagx, flagy2)],
            width=3,
        )

        flag = Polygon(
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
        line = Line(
            uuid="ground_line",
            color="#964B00",
            points=xys,
            width=1,
            fill_below=True,
        )

        return [
            car_sprite.as_dict(),
            line.as_dict(),
            flag_pole.as_dict(),
            flag.as_dict(),
        ]


env = MountainCarRGBEnv(render_mode="interactive-gym")
env
