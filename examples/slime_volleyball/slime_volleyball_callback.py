import typing
import time
import collections
import os

from slime_volleyball import slimevolley_env
import pandas as pd

from server import callback
from server.remote_game import RemoteGame


class SlimeVolleyballCallback(callback.GameCallback):

    def __init__(self) -> None:
        self.start_times = {}
        self.states = collections.defaultdict(list)
        self.actions = collections.defaultdict(list)
        self.rewards = collections.defaultdict(list)

    def on_episode_start(self, remote_game: RemoteGame) -> None:
        self.start_times[remote_game.game_uuid] = time.time()

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

    def on_game_end(self, remote_game: RemoteGame) -> None:

        print("game ending!")

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
        data_dir = f"data/slime_volleyball/"

        print(
            "writing data to",
            os.path.join(
                os.getcwd(), os.path.join(data_dir, f"{remote_game.game_uuid}.csv")
            ),
        )
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        game_data.to_csv(os.path.join(data_dir, f"{remote_game.game_uuid}.csv"))

        # clear out data
        del self.start_times[remote_game.game_uuid]
        del self.states[remote_game.game_uuid]
        del self.actions[remote_game.game_uuid]
        del self.rewards[remote_game.game_uuid]

    def gen_game_data(self, remote_game: RemoteGame) -> dict[str, typing.Any]:
        data = {
            "game_uuid": remote_game.game_uuid,
            "game_id": remote_game.game_id,
            "episode_num": remote_game.episode_num,
            "episode_s_elapsed": time.time() - self.start_times[remote_game.game_uuid],
            "tick_num": remote_game.tick_num,
        }

        env: slimevolley_env.SlimeVolleyEnv = remote_game.env
        data["agent_right_observation"] = env.game.agent_right.get_observation()
        data["agent_left_observation"] = env.game.agent_right.get_observation()

        for agent_id, player_name in remote_game.human_players.items():
            data[f"{agent_id}_identifier"] = player_name
            data[f"{agent_id}_is_human"] = True

        for agent_id, bot_id in remote_game.bot_players.items():
            data[f"{agent_id}_identifier"] = bot_id
            data[f"{agent_id}_is_human"] = False

        return data
