import collections
import queue
import dataclasses
import threading

import gymnasium as gym

from server import utils
from configurations import remote_config


@dataclasses.dataclass(frozen=True)
class GameStatus:
    Done = "done"
    Active = "active"
    Inactive = "inactive"
    Reset = "reset"


@dataclasses.dataclass(frozen=True)
class PolicyTypes:
    Human = "human"
    Random = "random"


class RemoteGame:
    def __init__(self, config: remote_config.RemoteConfig, game_id: int):
        self.config = config
        self.status = GameStatus.Inactive
        self.lock = threading.Lock()

        # Players and actions
        self.pending_actions = collections.defaultdict(lambda: queue.Queue(maxsize=1))
        self.human_players = {}
        self.bot_players = {}
        self.bot_threads = {}
        self._load_policies()

        # Game environment
        self.env = None
        self.obs = None
        self.game_id = game_id  # this will be set as the subjects socket id
        self.tick_num = 0
        self.episode_num = 0

    def tick(self):
        return self.status

    def _build_env(self) -> None:
        self.env = self.config.env_creator(**self.config.env_config)

    def _load_policies(self) -> None:
        """Load and instantiates all policies"""
        for agent_id, policy_id in self.config.policy_mapping.items():
            if policy_id == PolicyTypes.Human:
                self.human_players[agent_id] = utils.Available
            elif policy_id == PolicyTypes.Random:
                self.bot_players[agent_id] = policy_id
            else:
                assert (
                    self.config.load_policy_fn is not None
                ), "Must provide a method to load policies via policy name to RemoteConfig!"
                self.bot_players[agent_id] = self.config.load_policy_fn(policy_id)

    def get_available_human_player_ids(self) -> list[str]:
        """List the available human player IDs"""
        return [pid for pid, player in self.human_players if player is utils.Available]

    def is_at_player_capacity(self) -> bool:
        """Check if there are any available human player IDs."""
        return not self.get_available_human_player_ids()

    def cur_num_human_players(self) -> int:
        return len(
            [pid for pid, sid in self.human_players.items() if sid != utils.Available]
        )

    def remove_human_player(self, subject_id) -> None:
        """Remove a human player from the game"""
        player_id = None
        for pid, sid in self.human_players.items():
            if subject_id == sid:
                player_id = pid
                break

        if player_id is None:
            print(f"Attempted to remove {subject_id} but player wasn't found.")
            return

        self.human_players[player_id] = utils.Available

    def is_ready_to_start(self) -> bool:
        ready = self.is_at_player_capacity()
        return ready

    def build(self):
        self._build_env()

    def tear_down(self):
        self.status = GameStatus.Inactive
        for q in self.pending_actions.values():
            q.queue.clear()

    def enqueue_action(self, subject_id, action):
        if self.status != GameStatus.Active:
            return

        if subject_id not in self.human_players.values():
            return

        try:
            self.pending_actions[subject_id].put(action)
        except queue.Full:
            pass

    def add_player(self, player_id: str | int, identifier: str | int):
        available_ids = self.get_available_human_player_ids()
        assert (
            player_id in available_ids
        ), f"Player ID is not available! Available IDs are: {available_ids}"

        self.human_players[player_id] = identifier

    def step(self, actions: dict[str, int] | int):
        self.obs, rewards, terminateds, truncateds, _ = self.env.step(actions)
        print(f"step={self.tick_num}, actions={actions}, rewards={rewards}")

        if self.is_multiagent:
            terminateds = terminateds["__all__"]
            truncateds = truncateds["__all__"]

        self.t += 1
        if terminateds or truncateds:
            print("Terminated!" if terminateds else "Truncated!")
            self.is_done = True
            self.closed = True
            self.t = 0
            self.episode_num += 1

    def reset(self, seed: int | None = None):
        self.obs, _ = self.env.reset(seed=seed)
        self.is_done = False


class RemoteGameOld:
    def __init__(
        self,
        env: gym.Env,
        human_agent_id: str | None = None,
        policy_handler: None = None,
        seed: int | None = None,
    ) -> None:
        self.env = env
        self.seed = seed
        self.closed = False
        self.human_agent_id = human_agent_id
        self.policy_handler = policy_handler
        self.obs = None
        self.pending_actions = queue.Queue(maxsize=1)
        self.id = 0  # this will be set as the subjects socket id
        self.t = 0
        self.episode_num = 0
        self.is_done = False

        self.is_multiagent: bool = hasattr(env, "_agent_ids")
        self.agent_ids: list[str] = env._agent_ids if self.is_multiagent else [None]

    def step(self, actions: dict[str, int] | int):
        self.obs, rewards, terminateds, truncateds, _ = self.env.step(actions)
        print(f"step={self.t}, actions={actions}, rewards={rewards}")

        if self.is_multiagent:
            terminateds = terminateds["__all__"]
            truncateds = truncateds["__all__"]

        self.t += 1
        if terminateds or truncateds:
            print("Terminated!" if terminateds else "Truncated!")
            self.is_done = True
            self.closed = True
            self.t = 0
            self.episode_num += 1

    def reset(self, seed: int | None = None):
        self.obs, _ = self.env.reset(seed=seed)
        self.is_done = False
