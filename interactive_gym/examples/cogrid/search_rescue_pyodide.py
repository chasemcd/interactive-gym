"""
This is a self-contained example of launching an Interactive Gym experiment with the
CoGrid Search and Rescue environment:

https://cogrid.readthedocs.io/en/latest/content/examples.html#module-cogrid.envs.search_rescue.search_rescue

"""

from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse

from interactive_gym.server import app
from interactive_gym.scenes import scene
from interactive_gym.scenes import stager
from interactive_gym.examples.cogrid.pyodide_overcooked import (
    scenes as oc_scenes,
)
from interactive_gym.scenes import static_scene, gym_scene
from interactive_gym.configurations import experiment_config

from interactive_gym.configurations.object_contexts import Line, Polygon, Circle
from cogrid.envs.search_rescue import search_rescue
from cogrid.envs.search_rescue import search_rescue_grid_objects
from cogrid.core import grid_object


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


start_scene = (
    static_scene.StartScene()
    .scene(
        scene_id="search_rescue_start_scene",
        experiment_config={},
        should_export_metadata=True,
    )
    .display(
        scene_header="Welcome",
        scene_body="Welcome to the Search and Rescue environment demo!",
    )
)


search_rescue_gym_scene = (
    gym_scene.GymScene()
    .scene(scene_id="cramped_room_sp_0", experiment_config={})
    .policies(policy_mapping={0: "human", 1: "random"}, frame_skip=5)
    .rendering(
        fps=30,
        game_width=overcooked_utils.TILE_SIZE * 7,
        game_height=overcooked_utils.TILE_SIZE * 6,
        background="#e6b453",
    )
    .gameplay(
        default_action=Noop,
        action_mapping=action_mapping,
        num_episodes=1,
        max_steps=1350,
        input_mode=configuration_constants.InputModes.SingleKeystroke,
    )
    .user_experience(
        scene_header="Overcooked",
        scene_body="<center><p>"
        "This is an example environment using the Search and Rescue tak."
        "When the button activates, click it to begin. "
        "</p></center>",
        game_page_html_fn=overcooked_utils.overcooked_game_page_header_fn,
        in_game_scene_body="""
        <center>
        <p>
        TODO: Add controls description.
        </p>
        </center>
        <br><br>
        """,
    )
    .pyodide(
        run_through_pyodide=True,
        environment_initialization_code_filepath="interactive_gym/examples/cogrid/pyodide_overcooked/env_initialization/cramped_room_environment_initialization.py",
        packages_to_install=["numpy", "cogrid==0.0.16", "opencv-python"],
    )
)

end_scene = (
    static_scene.EndScene()
    .scene(
        scene_id="search_rescue_end_scene",
        should_export_metadata=True,
        experiment_config={},
    )
    .display(
        scene_header="Thank you for playing!",
        scene_body="You've completed the demo.",
    )
)

stager = stager.Stager(
    scenes=[
        start_scene,
        oc_scenes.tutorial_gym_scene,
        oc_scenes.cramped_room_0,
        end_scene,
    ]
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=5704, help="Port number to listen on"
    )
    args = parser.parse_args()

    experiment_config = (
        experiment_config.ExperimentConfig()
        .experiment(stager=stager, experiment_id="overcooked_test")
        .hosting(port=5704, host="0.0.0.0")
    )

    app.run(experiment_config)
