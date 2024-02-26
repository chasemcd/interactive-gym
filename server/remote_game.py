import collections
import dataclasses
import queue
import threading
import typing
import numpy as np
from gymnasium import spaces
import uuid

from configurations import remote_config
from configurations import configuration_constants
from server import utils
from absl import logging


@dataclasses.dataclass(frozen=True)
class GameStatus:
    Done = "done"
    Active = "active"
    Inactive = "inactive"
    Reset = "reset"


class RemoteGame:
    def __init__(self, config: remote_config.RemoteConfig, game_id: int):
        self.config = config
        self.status = GameStatus.Inactive
        self.lock = threading.Lock()
        self.reset_event = threading.Event()

        # Players and actions
        self.pending_actions = None
        self.reset_pending_actions()

        self.state_queues = None
        self.reset_state_queues()

        self.human_players = {}
        self.bot_players = {}
        self.bot_threads = {}

        # Game environment
        self.env = None
        self.obs: np.ndarray | dict[str, typing.Any] | None = None
        self.game_id = game_id
        assert (
            game_id is not None
        ), f"Must pass valid game id! Got {game_id} but expected an int."

        self.tick_num: int = 0
        self.game_uuid: str = str(uuid.uuid4())
        self.episode_num: int = 0
        self.episode_rewards = collections.defaultdict(lambda: 0)
        self.total_rewards = collections.defaultdict(lambda: 0)  # score across episodes
        self.total_positive_rewards = collections.defaultdict(
            lambda: 0
        )  # sum of positives
        self.total_negative_rewards = collections.defaultdict(
            lambda: 0
        )  # sum of negatives
        self.prev_rewards: dict[str | int, float] = {}
        self.prev_actions: dict[str | int, str | int] = {}

        self._build()

    def _build_env(self) -> None:
        self.env = self.config.env_creator(
            **self.config.env_config, render_mode="rgb_array"
        )

    def _load_policies(self) -> None:
        """Load and instantiates all policies"""
        for agent_id, policy_id in self.config.policy_mapping.items():
            if policy_id == configuration_constants.PolicyTypes.Human:
                self.human_players[agent_id] = utils.Available
            elif policy_id == configuration_constants.PolicyTypes.Random:
                self.bot_players[agent_id] = policy_id
            else:
                assert (
                    self.config.load_policy_fn is not None
                ), "Must provide a method to load policies via policy name to RemoteConfig!"
                self.bot_players[agent_id] = self.config.load_policy_fn(policy_id)

                # TODO(chase): put this in a separate function
                # self.bot_threads[agent_id] = threading.Thread(
                #     target=self.policy_consumer, args=(agent_id,)
                # )

    def policy_consumer(self, agent_id: str | int) -> None:
        while self.status == GameStatus.Active:
            try:
                state = self.state_queues[agent_id].get(block=False)
            except queue.Empty:
                continue

            policy = self.bot_players[agent_id]
            action = self.config.policy_inference_fn(state, policy)
            self.enqueue_action(agent_id, action)

    def get_available_human_player_ids(self) -> list[str]:
        """List the available human player IDs"""
        return [
            pid
            for pid, player in self.human_players.items()
            if player is utils.Available
        ]

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
            logging.warning(
                f"Attempted to remove {subject_id} but player wasn't found."
            )
            return

        self.human_players[player_id] = utils.Available

    def is_ready_to_start(self) -> bool:
        ready = self.is_at_player_capacity()
        return ready

    def _build(self):
        self._build_env()
        self._load_policies()

    def tear_down(self):
        self.status = GameStatus.Inactive

        for bot_thread in self.bot_threads.values():
            bot_thread.join()

        for q in self.pending_actions.values():
            q.queue.clear()

    def enqueue_action(self, subject_id, action) -> None:
        """Queue an action for a human player"""
        if self.status != GameStatus.Active:
            return

        try:
            self.pending_actions[subject_id].put(action, block=False)
        except queue.Full:
            pass

    def add_player(self, player_id: str | int, identifier: str | int) -> None:
        available_ids = self.get_available_human_player_ids()
        assert (
            player_id in available_ids
        ), f"Player ID is not available! Available IDs are: {available_ids}"

        self.human_players[player_id] = identifier

    def tick(self) -> None:

        # If the queue is empty, we have a mechanism for deciding which action to submit
        # Either the previous submitted action or the default action.
        player_actions = {}
        for pid, sid in self.human_players.items():
            action = None
            # Attempt to get an action from the action queue
            # If there's no action, use default or previous depending
            # on the method specified.
            try:
                action = self.pending_actions[sid].get(block=False)
            except queue.Empty:
                if (
                    self.config.action_population_method
                    == configuration_constants.ActionSettings.PreviousSubmittedAction
                ):
                    action = self.prev_actions.get(pid)

            if action is None:
                action = self.config.default_action

            player_actions[pid] = action

        #     if self.pending_actions[sid].qsize() > 0:

        # if self.config.action_population_method:
        #     default_action = self.pending_actions
        # player_actions = {
        #     pid: (
        #         self.pending_actions[sid].get(block=False)
        #         if self.pending_actions[sid].qsize() > 0
        #         else self.config.default_action
        #     )
        #     for pid, sid in self.human_players.items()
        # }

        # Bot actions
        for pid, bot in self.bot_players.items():

            # set default action
            # TODO(chase): add option for this to be the previous action
            if (
                self.config.action_population_method
                == configuration_constants.ActionSettings.PreviousSubmittedAction
            ):
                action = self.prev_actions.get(pid)
                if action is None:
                    action = self.config.default_action
                player_actions[pid] = self.config.default_action
            elif (
                self.config.action_population_method
                == configuration_constants.ActionSettings.DefaultAction
            ):
                player_actions[pid] = self.config.default_action
            else:
                raise NotImplementedError(
                    f"Action population method logic not specified for method: {self.config.action_population_method}"
                )

            # If the bot is random, just sample the action space at
            # frame_skip intervals
            if (
                bot == configuration_constants.PolicyTypes.Random
                and self.tick_num % self.config.frame_skip == 0
            ):
                if isinstance(self.env.action_space, spaces.Dict) or isinstance(
                    self.env.action_space, dict
                ):
                    player_actions[pid] = self.env.action_space[pid].sample()
                else:
                    player_actions[pid] = self.env.action_space.sample()

            # If we have a specified policy, pop an action from the pending actions queue
            # if there are any
            # TODO(Chase): figure out why this was hanging
            # elif self.pending_actions[pid].qsize() > 0:
            #     player_actions[pid] = self.pending_actions[pid].get(block=False)
            elif self.tick_num % self.config.frame_skip == 0:
                player_actions[pid] = self.config.policy_inference_fn(
                    self.obs[pid], bot
                )

        self.prev_actions = player_actions
        try:
            self.obs, rewards, terminateds, truncateds, _ = self.env.step(
                player_actions
            )

        except AssertionError:
            player_actions = list(player_actions.values())[0]
            self.obs, rewards, terminateds, truncateds, _ = self.env.step(
                player_actions
            )

        self.prev_rewards = (
            rewards if isinstance(rewards, dict) else {"reward": rewards}
        )

        # print("queuing obs")
        # if self.tick_num % self.config.frame_skip == 0:
        #     self.enqueue_observations()

        if not isinstance(rewards, dict):
            self.episode_rewards[0] += rewards
            self.total_rewards[0] += rewards
        else:
            for k, v in rewards.items():
                self.episode_rewards[k] += v
                self.total_rewards[k] += v
                self.total_positive_rewards[k] += max(0, v)
                self.total_negative_rewards[k] += min(0, v)

        if isinstance(terminateds, dict):
            terminateds = terminateds["__all__"]
            truncateds = truncateds["__all__"]

        self.tick_num += 1
        if terminateds or truncateds:
            if self.episode_num < self.config.num_episodes:
                self.status = GameStatus.Reset
            else:
                self.status = GameStatus.Done

    def enqueue_observations(self) -> None:
        """Add self.obs to the state queues for all bots"""
        if self.status != GameStatus.Active:
            return

        a = "b"
        for pid, obs in self.obs.items():
            if pid not in self.bot_players:
                continue

            try:
                self.state_queues[pid].put(obs, block=False)
            except queue.Full:
                pass

    def reset_pending_actions(self) -> None:
        self.pending_actions = collections.defaultdict(lambda: queue.Queue(maxsize=1))

    def reset_state_queues(self) -> None:
        self.state_queues = collections.defaultdict(lambda: queue.Queue(maxsize=1))

    def reset(self, seed: int | None = None) -> None:
        self.reset_pending_actions()
        self.prev_actions = {}
        self.prev_rewards = {}
        self.obs, _ = self.env.reset(seed=seed)
        self.status = GameStatus.Active

        self.tick_num = 0

        # if self.tick_num % self.config.frame_skip == 0:
        #     self.enqueue_observations()

        self.episode_num += 1
        self.episode_rewards = collections.defaultdict(lambda: 0)
