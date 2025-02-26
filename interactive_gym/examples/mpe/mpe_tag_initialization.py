import sys, types 
sys.modules["pygame"] = types.ModuleType("pygame")




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


# TODO: Validate this inheritance, does this correctly inherit from the MPE Tag parallel class?
class MPETagIG(simple_tag_v3.parallel_env):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_mode = "interactive_gym"

    def render(self, *arg, **kwargs) -> list[Circle]:
        #TODO: Look at the env instance and get the positions of the circles
        # For each of the circles, locate the position and return a Circle
        object_contexts = []

        mpe_world = self.unwrapped.world

        for agent_id in self.agents:
            idx = self.agents.index(agent_id)
            agent_obj = mpe_world.agents[idx]
            object_contexts.append(
                Circle(
                    uuid=agent_obj.uuid,  # using the underlying agent object's uuid
                    color=("#FF0000" if agent_obj.adversary else "#00FF00"),
                    x=(agent_obj.state.p_pos[0] + 1) / 2,
                    y=(agent_obj.state.p_pos[1] + 1) / 2,
                    radius=int(agent_obj.size * 100),
                )
            )

    # For landmarks (obstacles), assume they are stored in self.unwrapped.world.landmarks.
        for obstacle in self.unwrapped.world.landmarks:
            if obstacle.collide:  
                object_contexts.append(
                    Circle(
                        uuid=str(obstacle),
                        color="#000000",
                        x=(obstacle.state.p_pos[0] + 1) / 2,
                        y=(obstacle.state.p_pos[1] + 1) / 2,
                        radius=int(obstacle.size * 100),
                        permanent=True,
                    )
                )

        return object_contexts    

        # now find the obstacles and render them as black circles


# Keep these! They are needed for pyodide to access the environment
env = MPETagIG()
env
