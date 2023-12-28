# *
# game object dict
#     {
#         uuid: unique identifier
#         image_loc: path to image
#         sprite_sheet_loc: path to sprite sheet (if any)
#         object_type: object type, if not using an image
#         object_size: size of the object
#         x: relative x position [0, 1], multiplied by screen width
#         y: relative y position [0, 1], multiplied by screen height
#         orientation: direction facing (if applicable/using sprite sheet)
#         angle: should we rotate the sprite? In degrees.
#         depth: object depth (other things render on top?).
#         animation: name of the animation to play from a sprite sheet
#         animations: a list of animations to initialize from the sprite sheet
#                 format: anim = {key, frames, frameRate, repeat, hideOnComplete}
#     }
#  */
import typing
import dataclasses


@dataclasses.dataclass
class Sprite:
    """
    Context for a sprite object to render it. We maintain
    this for each object that we are tracking in the game
    state and passing along to render.
    """

    uuid: str
    x: int
    y: int
    image_name: str | None = None
    sprite_sheet_name: str | None = None
    object_size: int | None = None
    angle: int | None = None
    depth: int = 1
    animation: str | None = None
    object_type: str = "sprite"

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Line:
    uuid: str
    color: str
    width: int
    points: list[tuple[float, float]]
    object_type: str = "line"
    fill_below: bool = False
    fill_above: bool = False
    depth: int = -1

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Circle:
    uuid: str
    color: str
    x: float
    y: float
    radius: int
    alpha: float = 1
    object_type: str = "circle"
    depth: int = -1

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Polygon:
    uuid: str
    color: str
    points: list[tuple[float, float]]
    object_type: str = "polygon"
    depth: int = -1

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)
