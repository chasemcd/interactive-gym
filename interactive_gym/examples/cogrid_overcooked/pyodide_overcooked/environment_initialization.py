import functools

from cogrid.core import layouts
from cogrid.core import grid_object
from cogrid.envs import overcooked
from cogrid.envs.overcooked import overcooked_grid_objects
from cogrid.envs import registry


import dataclasses
import typing


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
    height: int
    width: int
    image_name: str | None = None  # texture name
    frame: str | int | None = None
    object_size: int | None = None
    angle: int | None = None
    depth: int = 1
    animation: str | None = None
    object_type: str = "sprite"
    tween: bool = False
    tween_duration: int = 50
    permanent: bool = False

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
    permanent: bool = False

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
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Polygon:
    uuid: str
    color: str
    points: list[tuple[float, float]]
    alpha: float = 1
    object_type: str = "polygon"
    depth: int = -1
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Text:
    uuid: str
    text: str
    x: float | int
    y: float | int
    size: int = 16
    color: str = "#000000"
    font: str = "Arial"
    depth: int = -1
    object_type: str = "text"
    permanent: bool = False

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class AtlasSpec:
    name: str
    img_path: str
    atlas_path: str
    object_type: str = "atlas_spec"

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class MultiAtlasSpec:
    name: str
    img_path: str
    atlas_path: str
    object_type: str = "multi_atlas_spec"

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ImgSpec:
    name: str
    img_path: str
    object_type: str = "img_spec"

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def get_x_y(
    pos: tuple[int, int], game_height: int, game_width: int
) -> tuple[int, int]:
    col, row = pos
    x = row * TILE_SIZE / game_width
    y = col * TILE_SIZE / game_height
    return x, y


ASSET_PATH = "static/assets/overcooked/sprites"
TILE_SIZE = 45
WIDTH = 12 * TILE_SIZE
HEIGHT = 7 * TILE_SIZE
DIR_TO_CARDINAL_DIRECTION = {
    0: "EAST",
    1: "SOUTH",
    2: "WEST",
    3: "NORTH",
}
PLAYER_COLORS = {0: "blue", 1: "green"}


def generate_counter_objects(env: overcooked.Overcooked) -> list[Sprite]:
    objs = []
    for obj in env.grid.grid:
        if not (
            isinstance(obj, grid_object.Counter)
            or isinstance(obj, grid_object.Wall)
            or isinstance(obj, overcooked_grid_objects.Pot)
        ):
            continue

        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)

        objs.append(
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="terrain",
                frame="counter.png",
                permanent=True,
                depth=-2,
            )
        )
    return objs


def generate_delivery_areas(
    env: overcooked.Overcooked,
) -> list[Sprite]:
    objs = []
    for obj in env.grid.grid:
        if not isinstance(obj, overcooked_grid_objects.DeliveryZone):
            continue
        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)

        objs.append(
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="terrain",
                frame="serve.png",
                permanent=True,
            )
        )
    return objs


def generate_static_tools(
    env: overcooked.Overcooked,
) -> list[Sprite]:
    objs = []
    for obj in env.grid.grid:
        if isinstance(obj, overcooked_grid_objects.PlateStack):
            x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
            objs.append(
                Sprite(
                    obj.uuid,
                    x=x,
                    y=y,
                    height=TILE_SIZE,
                    width=TILE_SIZE,
                    image_name="terrain",
                    frame="dishes.png",
                    permanent=True,
                )
            )
        elif isinstance(obj, overcooked_grid_objects.OnionStack):
            x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
            objs.append(
                Sprite(
                    obj.uuid,
                    x=x,
                    y=y,
                    height=TILE_SIZE,
                    width=TILE_SIZE,
                    image_name="terrain",
                    frame="onions.png",
                    permanent=True,
                )
            )
        elif isinstance(obj, overcooked_grid_objects.Pot):
            x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
            objs.append(
                Sprite(
                    obj.uuid,
                    x=x,
                    y=y,
                    height=TILE_SIZE,
                    width=TILE_SIZE,
                    image_name="terrain",
                    frame="pot.png",
                    permanent=True,
                )
            )

    return objs


def generate_agent_sprites(env: overcooked.Overcooked) -> list[Sprite]:
    objs = []
    for i, agent_obj in enumerate(env.grid.grid_agents.values()):
        x, y = get_x_y(agent_obj.pos, HEIGHT, WIDTH)
        held_object_name = ""
        if agent_obj.inventory:
            assert (
                len(agent_obj.inventory) == 1
            ), "Rendering not supported for inventory > 1."

            held_obj = agent_obj.inventory[0]
            if isinstance(held_obj, overcooked_grid_objects.Onion):
                held_object_name = "-onion"
            elif isinstance(held_obj, overcooked_grid_objects.OnionSoup):
                held_object_name = "-soup-onion"
            elif isinstance(held_obj, overcooked_grid_objects.Plate):
                held_object_name = "-dish"

        dir = DIR_TO_CARDINAL_DIRECTION[agent_obj.dir]

        objs.append(
            Sprite(
                f"agent-{i}-sprite",
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="chefs",
                tween=True,
                frame=f"{dir}{held_object_name}.png",
            )
        )

        objs.append(
            Sprite(
                f"agent-{i}-hat-sprite",
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="chefs",
                frame=f"{dir}-{PLAYER_COLORS[i]}hat.png",
                tween=True,
                depth=2,
            )
        )
    return objs


def generate_objects(
    env: overcooked.Overcooked,
) -> list[Sprite]:
    objs = []
    for obj in env.grid.grid:
        if obj is None:
            continue

        if obj.can_place_on and obj.obj_placed_on is not None:
            objs += temp_object_creation(obj=obj.obj_placed_on)

        objs += temp_object_creation(obj=obj)

    return objs


def temp_object_creation(obj: grid_object.GridObj):
    if isinstance(obj, overcooked_grid_objects.Pot):
        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
        if not obj.objects_in_pot:
            return []
        status = "cooked" if obj.cooking_timer == 0 else "cooking"
        if status == "cooking":
            frame = f"soup-onion-{len(obj.objects_in_pot)}-cooking.png"
        else:
            frame = "soup-onion-cooked.png"

        pot_sprite = [
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="objects",
                frame=frame,
                depth=-1,
            )
        ]

        if status == "cooking" and len(obj.objects_in_pot) == 3:
            pot_sprite.append(
                Text(
                    uuid="time_left",
                    text=f"{obj.cooking_timer:02d}",
                    x=x,
                    y=y,
                    size=14,
                    color="red",
                )
            )

        return pot_sprite
    elif isinstance(obj, overcooked_grid_objects.Onion):
        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
        return [
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="objects",
                frame="onion.png",
                depth=-1,
            )
        ]

    elif isinstance(obj, overcooked_grid_objects.Plate):
        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
        return [
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="objects",
                frame="dish.png",
                depth=-1,
            )
        ]
    elif isinstance(obj, overcooked_grid_objects.OnionSoup):
        x, y = get_x_y(obj.pos, HEIGHT, WIDTH)
        return [
            Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="objects",
                frame="soup-onion-dish.png",
                depth=-1,
            )
        ]
    return []


class InteractiveGymOvercooked(overcooked.Overcooked):

    def env_to_render_fn(self):
        render_objects = []

        if self.t == 0:
            render_objects += self.generate_counter_objects(env=self)
            render_objects += self.generate_delivery_areas(env=self)
            render_objects += self.generate_static_tools(env=self)

        render_objects += self.generate_agent_sprites(env=self)
        render_objects += self.generate_objects(env=self)

        return [obj.as_dict() for obj in render_objects]


overcooked_config = {
    "name": "overcooked",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "features": ["overcooked_features"],
    "rewards": ["delivery_reward"],
    "grid": {"layout": "overcooked_cramped_room_v0"},
    "max_steps": 1000,
    "scope": "overcooked",
}

registry.register(
    environment_id="Overcooked-RandomizedLayout-EnvToRender",
    env_class=functools.partial(
        InteractiveGymOvercooked, config=overcooked_config
    ),
)

env = registry.make("Overcooked-RandomizedLayout-EnvToRender")
