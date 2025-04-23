import functools

from cogrid.envs.search_rescue import search_rescue
from cogrid.envs.search_rescue import search_rescue_grid_objects
from cogrid.core import grid_object
from interactive_gym.configurations import (
    configuration_constants,
)
from interactive_gym.configurations.object_contexts import Line, Polygon, Circle
from cogrid.envs import registry


class SearchRescueIG(search_rescue.SearchRescueEnv):
    TILE_SIZE = 45
    OBJ_TO_COLOR = {
        "agent_0": "#4169E1",  # Royal Blue
        "agent_1": "#8A2BE2",  # Blue Violet
        "pickaxe": "#A0522D",  # Brown
        "rubble": "#CD853F",  # Peru (sandy brown)
        "med_kit": "#FF4444",  # Bright Red
        "key": "#FFD700",  # Gold
        "green_victim": "#32CD32",  # Lime Green
        "yellow_victim": "#FFD700",  # Gold
        "red_victim": "#FF0000",  # Red
        "door": "#8B4513",  # Saddle Brown
        "wall": "#404040",  # Dark Grey
    }

    def render(self):
        if self.render_mode != "interactive_gym":
            return super().render()

        render_objects = []
        # Add permanent wall objects at t == 0 since they're never updated
        if self.t == 0:
            for obj in self.grid.grid:
                if isinstance(obj, grid_object.Wall):
                    render_objects.append(
                        Polygon(
                            uuid=obj.uuid,
                            color=self.OBJ_TO_COLOR["wall"],
                            points=self.get_square_points(obj.pos),
                            permanent=True,
                        )
                    )

        # Render each of:
        # Agents, Pickaxe, Rubble, Med Kit, Key,
        # Green Victim, Yellow Victim, Red Victim, Doors (open vs closed)
        for obj in self.grid.grid:
            if isinstance(
                obj,
                (
                    search_rescue_grid_objects.RedVictim,
                    search_rescue_grid_objects.YellowVictim,
                    search_rescue_grid_objects.GreenVictim,
                ),
            ):
                victim_color = self.OBJ_TO_COLOR[obj.name]
                x, y = self.get_x_y(obj.pos, self.grid.height, self.grid.width)
                render_objects.append(
                    Circle(
                        uuid=obj.uuid,
                        color=victim_color,
                        x=x,
                        y=y,
                        radius=self.TILE_SIZE / 2,
                    )
                )

            elif isinstance(obj, grid_object.Door):
                door_is_open = obj.state == 1
                if door_is_open:
                    continue

                door_color = self.OBJ_TO_COLOR["door"]
                render_objects.append(
                    Polygon(
                        uuid=obj.uuid,
                        color=door_color,
                        points=self.get_square_points(obj.pos),
                    )
                )

            elif isinstance(obj, search_rescue_grid_objects.Pickaxe):
                pickaxe_color = self.OBJ_TO_COLOR["pickaxe"]
                x, y = self.get_x_y(obj.pos, self.grid.height, self.grid.width)
                render_objects.append(
                    Polygon(
                        uuid=obj.uuid,
                        color=pickaxe_color,
                        points=self.get_square_points(obj.pos),
                    )
                )

            elif isinstance(obj, search_rescue_grid_objects.MedKit):
                medkit_color = self.OBJ_TO_COLOR["med_kit"]
                x, y = self.get_x_y(obj.pos, self.grid.height, self.grid.width)
                render_objects.append(
                    Polygon(
                        uuid=obj.uuid,
                        color=medkit_color,
                        points=self.get_square_points(obj.pos),
                    )
                )

            elif isinstance(obj, grid_object.Key):
                key_color = self.OBJ_TO_COLOR["key"]
                x, y = self.get_x_y(obj.pos, self.grid.height, self.grid.width)
                render_objects.append(
                    Polygon(
                        uuid=obj.uuid,
                        color=key_color,
                        points=self.get_square_points(obj.pos),
                    )
                )

            elif isinstance(obj, search_rescue_grid_objects.Rubble):
                rubble_color = self.OBJ_TO_COLOR["rubble"]
                x, y = self.get_x_y(obj.pos, self.grid.height, self.grid.width)
                render_objects.append(
                    Polygon(
                        uuid=obj.uuid,
                        color=rubble_color,
                        points=self.get_square_points(obj.pos),
                    )
                )

        for i, agent_obj in enumerate(self.grid.grid_agents.values()):
            x, y = self.get_x_y(
                agent_obj.pos, self.grid.height, self.grid.width
            )

            # Add a triangle using the polygon, the point should be facing in the agent's direction
            agent_dir = agent_obj.dir
            agent_dir_to_triangle_points = {
                "up": [
                    (x, y - self.TILE_SIZE / 2),
                    (x + self.TILE_SIZE / 2, y + self.TILE_SIZE / 2),
                    (x - self.TILE_SIZE / 2, y + self.TILE_SIZE / 2),
                ],
                "down": [
                    (x, y + self.TILE_SIZE / 2),
                    (x + self.TILE_SIZE / 2, y - self.TILE_SIZE / 2),
                    (x - self.TILE_SIZE / 2, y - self.TILE_SIZE / 2),
                ],
                "left": [
                    (x - self.TILE_SIZE / 2, y),
                    (x + self.TILE_SIZE / 2, y - self.TILE_SIZE / 2),
                    (x + self.TILE_SIZE / 2, y + self.TILE_SIZE / 2),
                ],
                "right": [
                    (x + self.TILE_SIZE / 2, y),
                    (x - self.TILE_SIZE / 2, y - self.TILE_SIZE / 2),
                    (x - self.TILE_SIZE / 2, y + self.TILE_SIZE / 2),
                ],
            }
            triangle_points = agent_dir_to_triangle_points[agent_dir]
            render_objects.append(
                Polygon(
                    uuid=f"agent-{i}-triangle",
                    color=self.OBJ_TO_COLOR["agent_0"],
                    points=triangle_points,
                )
            )

            if agent_obj.inventory:
                # If they're holding anything, render a small square in the bottom right of the cell
                grid_object_name = agent_obj.inventory[0].name
                grid_object_color = self.OBJ_TO_COLOR[grid_object_name]
                render_objects.append(
                    Polygon(
                        uuid=f"agent-{i}-inventory-{grid_object_name}",
                        color=grid_object_color,
                        points=self.get_square_points(agent_obj.pos),
                        alpha=0.5,
                        depth=5,
                    )
                )

        return [obj.to_dict() for obj in render_objects]

    def get_x_y(
        self, pos: tuple[int, int], game_height: int, game_width: int
    ) -> tuple[int, int]:
        col, row = pos
        x = row * self.TILE_SIZE / self.grid.height
        y = col * self.TILE_SIZE / self.grid.width
        return x, y

    def get_square_points(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        # Get center point using existing get_x_y method
        center_x, center_y = self.get_x_y(
            pos, self.grid.height, self.grid.width
        )
        half_size = self.TILE_SIZE / 2

        # Calculate corners clockwise from top-left
        return [
            (center_x - half_size, center_y - half_size),  # Top-left
            (center_x + half_size, center_y - half_size),  # Top-right
            (center_x + half_size, center_y + half_size),  # Bottom-right
            (center_x - half_size, center_y + half_size),  # Bottom-left
        ]


sr_config = {
    "name": "search_rescue",
    "num_agents": 2,
    "action_set": "cardinal_actions",
    "obs": ["agent_positions"],
    "grid": {"layout": "search_rescue_test"},
    "max_steps": 1000,
    "common_reward": True,
    "scope": "search_rescue",
}


registry.register(
    environment_id="SearchRescueIG",
    env_class=functools.partial(SearchRescueIG, config=sr_config),
)

env = registry.make("SearchRescueIG")


env
