from __future__ import annotations

import collections
import logging
import os
import time
import typing

import pandas as pd
from cogrid import cogrid_env

from interactive_gym.server import callback
from interactive_gym.server.remote_game import RemoteGame

logger = logging.getLogger(__name__)


class OvercookedCallback(callback.GameCallback):

    def __init__(self) -> None:
        self.start_times = {}
        self.states = collections.defaultdict(list)
        self.actions = collections.defaultdict(list)
        self.rewards = collections.defaultdict(list)

    def on_episode_start(self, remote_game: RemoteGame) -> None:
        self.start_times[remote_game.game_uuid] = time.time()

    def on_episode_end(self, remote_game: RemoteGame) -> None:
        self.save_and_clear_data(remote_game)

    def on_game_tick_start(self, remote_game: RemoteGame) -> None:
        """
        At the beginning of the tick() call, we'll log the current state of the game.
        """
        self.states[remote_game.game_uuid].append(self.gen_game_data(remote_game))

    def on_game_tick_end(self, remote_game: RemoteGame) -> None:
        """
        At the end of the tick() call, log the actions taken and the reward earned.
        """
        actions = {
            f"{a_id}_action": action
            for a_id, action in remote_game.prev_actions.items()
        }
        rewards = {
            f"{a_id}_reward": reward
            for a_id, reward in remote_game.prev_rewards.items()
        }

        self.actions[remote_game.game_uuid].append(actions)
        self.rewards[remote_game.game_uuid].append(rewards)

    def gen_game_data(self, remote_game: RemoteGame) -> dict[str, typing.Any]:
        data = {
            "game_uuid": remote_game.game_uuid,
            "game_id": remote_game.game_id,
            "episode_num": remote_game.episode_num,
            "episode_s_elapsed": time.time() - self.start_times[remote_game.game_uuid],
            "tick_num": remote_game.tick_num,
        }

        env: cogrid_env.CoGridEnv = remote_game.env
        for agent_id, agent in env.grid.grid_agents.items():
            data[f"{agent_id}_pos"] = agent.pos
            data[f"{agent_id}_dir"] = agent.dir

        for agent_id, player_name in remote_game.human_players.items():
            data[f"{agent_id}_identifier"] = player_name
            data[f"{agent_id}_is_human"] = True
            data[f"{agent_id}_doc_in_focus"] = remote_game.document_focus_status[
                player_name
            ]
            data[f"{agent_id}_cur_ping"] = remote_game.current_ping[player_name]

        for agent_id, bot_id in remote_game.bot_players.items():
            data[f"{agent_id}_identifier"] = bot_id
            data[f"{agent_id}_is_human"] = False

        return data

    def save_and_clear_data(self, remote_game: RemoteGame) -> None:
        full_data_dicts = []

        # merge the list of dicts
        for state_data, action_data, reward_data in zip(
            self.states[remote_game.game_uuid],
            self.actions[remote_game.game_uuid],
            self.rewards[remote_game.game_uuid],
        ):
            state_data.update(action_data)
            state_data.update(reward_data)
            full_data_dicts.append(state_data)

        game_data = pd.DataFrame(full_data_dicts)
        data_dir = f"data/overcooked/"

        save_file_path = os.path.join(
            data_dir,
            f"{remote_game.game_uuid}-episode-{remote_game.episode_num}.csv",
        )

        logger.info(f"writing data to {save_file_path}")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        game_data.to_csv(save_file_path)

        # clear out data
        del self.start_times[remote_game.game_uuid]
        del self.states[remote_game.game_uuid]
        del self.actions[remote_game.game_uuid]
        del self.rewards[remote_game.game_uuid]
