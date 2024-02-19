import os

from cogrid.envs import overcooked
from cogrid.envs import overcooked_grid_objects
from cogrid.core import grid_object

from configurations import remote_config
from configurations import object_contexts

ASSET_PATH = "static/assets/"
TILE_SIZE = 16
DIR_TO_CARDINAL_DIRECTION = {
    0: "EAST",
    1: "SOUTH",
    2: "WEST",
    3: "NORTH",
}
PLAYER_COLORS = {0: "blue", 1: "green"}


def get_x_y(pos: tuple[int, int], game_height: int, game_width: int) -> tuple[int, int]:
    row, col = pos
    x = row * TILE_SIZE / game_width
    y = 1 - col * TILE_SIZE / game_height
    return x, y


def overcooked_preload_assets_spec() -> (
    list[
        object_contexts.AtlasSpec
        | object_contexts.MultiAtlasSpec
        | object_contexts.ImgSpec
    ]
):
    terrain = object_contexts.AtlasSpec(
        name="terrain",
        img_path=os.path.join(ASSET_PATH, "terrain.png"),
        atlas_path=os.path.join(ASSET_PATH, "terrain.json"),
    )
    chefs = object_contexts.AtlasSpec(
        name="chefs",
        img_path=os.path.join(ASSET_PATH, "chefs.png"),
        atlas_path=os.path.join(ASSET_PATH, "chefs.json"),
    )
    objects = object_contexts.AtlasSpec(
        name="objects",
        img_path=os.path.join(ASSET_PATH, "objects.png"),
        atlas_path=os.path.join(ASSET_PATH, "objects.json"),
    )
    # soups = object_contexts.MultiAtlasSpec(
    #     name="soups",
    #     img_path=os.path.join(ASSET_PATH, "soups.png"),
    #     atlas_path=os.path.join(ASSET_PATH, "soups.json"),
    # )

    return [terrain.as_dict(), chefs.as_dict(), objects.as_dict()]  # , soups.as_dict()]


def overcooked_env_to_render_fn(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
):
    render_objects = []

    if env.t == 0:
        render_objects += generate_counter_objects(env=env, config=config)
        render_objects += generate_delivery_areas(env, config=config)
        render_objects += generate_static_tools(env=env, config=config)

    render_objects += generate_agent_sprites(env=env, config=config)

    return [obj.as_dict() for obj in render_objects]


def generate_counter_objects(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]:
    objs = []
    for obj in env.grid.grid:
        if not (
            isinstance(obj, grid_object.Counter)
            or isinstance(obj, grid_object.Wall)
            or isinstance(obj, overcooked_grid_objects.Pot)
        ):
            continue

        x, y = get_x_y(obj.pos, config.game_height, config.game_width)

        objs.append(
            object_contexts.Sprite(
                obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="terrain",
                frame="counter.png",
                permanent=True,
            )
        )
    return objs


def generate_delivery_areas(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]:
    objs = []
    for obj in env.grid.grid:
        if not isinstance(obj, overcooked_grid_objects.DeliveryZone):
            continue
        x, y = get_x_y(obj.pos, config.game_height, config.game_width)

        objs.append(
            object_contexts.Sprite(
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
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]:
    objs = []
    for obj in env.grid.grid:

        if isinstance(obj, overcooked_grid_objects.PlateStack):
            x, y = get_x_y(obj.pos, config.game_height, config.game_width)
            objs.append(
                object_contexts.Sprite(
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
            x, y = get_x_y(obj.pos, config.game_height, config.game_width)
            objs.append(
                object_contexts.Sprite(
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

    return objs


def generate_agent_sprites(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]:
    objs = []
    for i, agent_obj in enumerate(env.grid.grid_agents.values()):
        x, y = get_x_y(agent_obj.pos, config.game_height, config.game_width)
        print(x, y)
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

        dir = DIR_TO_CARDINAL_DIRECTION[agent_obj.dir]

        objs.append(
            object_contexts.Sprite(
                agent_obj.uuid,
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="chefs",
                frame=f"{dir}{held_object_name}.png",
            )
        )

        objs.append(
            object_contexts.Sprite(
                f"hat-{agent_obj.uuid}",
                x=x,
                y=y,
                height=TILE_SIZE,
                width=TILE_SIZE,
                image_name="chefs",
                frame=f"{dir}-{PLAYER_COLORS[i]}hat.png",
                depth=2,
            )
        )
    return objs
