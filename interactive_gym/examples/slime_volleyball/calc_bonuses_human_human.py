from __future__ import annotations

import os

import numpy as np
import pandas as pd

DATA_PATH = "data/slime_vb_hh_0318"


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
            "agent_right_identifier",
            "agent_left_cur_ping",
            "agent_right_cur_ping",
            "agent_left_reward",
            "agent_right_reward",
            "agent_left_action",
            "agent_right_action",
            "agent_left_doc_in_focus",
            "agent_right_doc_in_focus",
        ]
    ]
    df["agent_left_action_is_noop"] = df["agent_left_action"] == 0
    df["agent_right_action_is_noop"] = df["agent_right_action"] == 0

    df["num_episodes"] = df.groupby("game_uuid")["episode_num"].transform("max")
    df["count"] = 1
    df["agent_left_reward"] = df["agent_left_reward"].apply(lambda x: max(0, x))
    df["agent_right_reward"] = df["agent_right_reward"].apply(lambda x: max(0, x))
    df["agent_right_doc_in_focus"] = (
        df["agent_right_doc_in_focus"]
        .map(lambda x: x if not pd.isna(x) else 0)
        .astype(int)
    )
    df["agent_left_doc_in_focus"] = (
        df["agent_left_doc_in_focus"]
        .map(lambda x: x if not pd.isna(x) else 0)
        .astype(int)
    )

    df.rename(
        columns={
            "agent_left_identifier": "agent_left_mturk_id",
            "agent_right_identifier": "agent_right_mturk_id",
        },
        inplace=True,
    )
    df = df[
        df.agent_left_mturk_id.apply(
            lambda x: len(str(x)) in [12, 13, 14, 15] and str(x)[0] == "A"
        )
    ]

    result = (
        df.groupby(["agent_left_mturk_id", "agent_right_mturk_id"])
        .sum(numeric_only=True)
        .reset_index()
    )

    result["agent_right_proportion_noop"] = (
        result["agent_right_action_is_noop"] / result["count"]
    )
    result["agent_left_proportion_noop"] = (
        result["agent_left_action_is_noop"] / result["count"]
    )

    result["agent_left_prop_in_focus"] = (
        result["agent_left_doc_in_focus"] / result["count"]
    )
    result["agent_right_prop_in_focus"] = (
        result["agent_right_doc_in_focus"] / result["count"]
    )

    result.drop(
        columns=[
            "agent_left_action",
            "agent_left_action_is_noop",
            "agent_right_action",
            "agent_right_action_is_noop",
        ],
        inplace=True,
    )

    result["left_bonus"] = result["agent_left_reward"] * 0.05
    result["right_bonus"] = result["agent_right_reward"] * 0.05
    result["right_bonus"] = result["right_bonus"].apply(
        lambda x: np.round(min(x, 1.5), 2)
    )
    result["left_bonus"] = result["left_bonus"].apply(
        lambda x: np.round(min(x, 1.5), 2)
    )
    result = result.round(2)
    result.to_csv("data/slime_vb_human_human_bonuses.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
