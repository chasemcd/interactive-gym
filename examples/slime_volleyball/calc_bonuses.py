import os

import pandas as pd

DATA_PATH = "data/slime_volleyball/"


def read_files(data_path: str) -> pd.DataFrame:
    files = os.listdir(data_path)
    dfs = []
    for f in files:
        if not f.endswith(".csv"):
            continue

        df = pd.read_csv(os.path.join(data_path, f))
        dfs.append(df)

    concat_df = pd.concat(dfs)

    return concat_df


def calc_bonuses(df: pd.DataFrame) -> None:

    df = df[
        [
            "game_uuid",
            "episode_num",
            "agent_left_identifier",
            "agent_left_reward",
            "agent_left_action",
        ]
    ]
    df["action_is_noop"] = df["agent_left_action"] == 0
    df["max_episode_num"] = df.groupby("game_uuid")["episode_num"].transform("max")
    df = df[df.max_episode_num == 50]
    df = df.drop(columns=["max_episode_num"])
    df["count"] = 1
    df["agent_left_reward"] = df["agent_left_reward"].apply(lambda x: max(0, x))

    df.rename(
        columns={"agent_left_identifier": "mturk_id", "agent_left_reward": "score"},
        inplace=True,
    )

    result = df.groupby("mturk_id").sum(numeric_only=True).reset_index()

    result["proportion_noop"] = result["action_is_noop"] / result["count"]

    result.drop(columns=["agent_left_action", "action_is_noop"], inplace=True)

    result["bonus"] = result["score"] * 0.03
    result["bonus"] = result["bonus"].apply(lambda x: min(x, 1.5))
    result.to_csv("data/slime_vb_human_ai_bonuses.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
