from pettingzoo.mpe import simple_tag_v3
import dataclasses
import typing


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


class MPETagIG(simple_tag_v3.parallel_env):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_mode = "interactive_gym"

    def render(self, *arg, **kwargs) -> list[Circle]:
        # TODO: Look at the env instance and get the positions of the circles
        # For each of the circles, locate the position and return a Circle
        object_contexts = []
        for circle in env.agents:
            object_contexts.append(
                Circle(
                    uuid=circle.uuid,
                    color=(
                        "red" if adversary else "green"
                    ),  # convert to hex code
                    x=circle.x,  # X should be relative to the total size and be in [0, 1]. Base it on the max width of the env
                    y=circle.y,  # Y should be relative to the total size and be in [0, 1]. Base it on the max height of the env
                    radius=circle.radius,  # radius should be in pixels
                )
            )

        # now find the obstacles and render them as black circles
        ...


# Keep these! They are needed for pyodide to access the environment
env = MPETagIG()
env
