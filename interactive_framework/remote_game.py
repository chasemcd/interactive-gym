import gymnasium as gym
from ray import rllib
import queue

from interactive_framework import policy_wrapper


class RemoteGame:
    def __init__(
        self,
        env: gym.Env | rllib.env.MultiAgentEnv,
        human_agent_id: str | None = None,
        policy_handler: policy_wrapper.MultiAgentPolicyWrapper | None = None,
        seed: int = None,
    ) -> None:
        self.env = env
        self.seed = seed
        self.closed = False
        self.human_agent_id = human_agent_id
        self.policy_handler: policy_wrapper.MultiAgentPolicyWrapper | None = policy_handler
        self.obs = None
        self.cumulative_reward = 0
        self.pending_actions = queue.Queue(maxsize=1)
        self.id = 0  # this will be set as the subjects socket id
        self.t = 0

        self.is_multiagent: bool = hasattr(env, "_agent_ids")
        self.agent_ids = env._agent_ids if self.is_multiagent else [None]

    def step(self, actions: dict[str, int] | int):
        self.obs, rewards, terminateds, truncateds, _ = self.env.step(actions)
        self.cumulative_reward += (
            sum([*rewards.values()]) if isinstance(rewards, dict) else rewards
        )
        print(
            f"step={self.t}, actions={actions}, rewards={rewards}, cumulative_reward={self.cumulative_reward}"
        )

        if self.is_multiagent:
            terminateds = terminateds["__all__"]
            truncateds = truncateds["__all__"]

        if terminateds or truncateds:
            print("Terminated!" if terminateds else "Truncated!")
            self.closed = True
            self.reset(self.seed)
            self.t = 0
        else:
            self.t += 1
            return self.env.render()

    def reset(self, seed):
        self.obs, _ = self.env.reset(seed=seed)
        self.cumulative_reward = 0
        self.env.render()
