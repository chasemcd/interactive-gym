from cogrid.envs import overcooked
from cogrid.envs import overcooked_grid_objects

from configurations import remote_config
from configurations import object_contexts


def overcooked_env_to_render_fn(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
):
    render_objects = []

    if env.t == 0:
        # render_objects += generate_counter_objects(env=env, config=config)
        # render_objects += generate_wall_objects(env=env, config=config)
        # render_objects += generate_delivery_areas(env)
        render_objects += generate_static_tools(env=env, config=config)

    return [obj.as_dict() for obj in render_objects]


def generate_counter_objects(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]: ...


def generate_wall_objects(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]: ...


# def generate_agent_objects(
#     env: overcooked.Overcooked, config: remote_config.RemoteConfig
# ) -> list[object_contexts.Sprite]:
#     agent_objects = []
#     for agent_obj in env.grid.grid_agents:
#         obj = object_contexts.Sprite(
#             uuid=f"{agent_obj.name}_{agent_obj.uuid}",
#             x=agent_obj.pos[0] * 32 / config.game_width,
#             y=1 - agent_obj.pos[1] * 32 / config.game_height,
#             image_name=img,
#         )


def generate_static_tools(
    env: overcooked.Overcooked, config: remote_config.RemoteConfig
) -> list[object_contexts.Sprite]:
    static_tool_objects = []
    for grid_obj in env.grid.grid:
        if isinstance(grid_obj, overcooked_grid_objects.PlateStack):
            img = "examples/cogrid_overcooked/assets/empty_bowl.png"
        elif isinstance(grid_obj, overcooked_grid_objects.OnionStack):
            img = "examples/cogrid_overcooked/assets/onion.png"
        else:
            continue

        obj = object_contexts.Sprite(
            uuid=f"{grid_obj.object_id}_{grid_obj.uuid}",
            x=grid_obj.pos[0] * 32 / config.game_width,
            y=1 - grid_obj.pos[1] * 32 / config.game_height,
            image_name=img,
        )

        static_tool_objects.append(obj)

    return static_tool_objects
