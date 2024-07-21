from __future__ import annotations

import os

import pandas as pd

DATA_PATH = "data/overcooked/0311/overcooked"


def read_files(data_path: str) -> pd.DataFrame:
    files = os.listdir(data_path)
    dfs = []
    for f in files:
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(data_path, f))
        except Exception as e:
            print(f, e)
            continue
        dfs.append(df)

    concat_df = pd.concat(dfs)

    return concat_df


def calc_bonuses(df: pd.DataFrame) -> None:

    df = df[
        [
            "game_uuid",
            "agent-0_identifier",
            "agent-0_reward",
            "agent-0_action",
            "episode_num",
            "agent-0_doc_in_focus",
            # "agent-1_doc_in_focus",
        ]
    ]
    df["count"] = 1
    df["action_is_noop"] = df["agent-0_action"] == 6.0
    df["max_episode_num"] = df.groupby("game_uuid")["episode_num"].transform("max")
    # df = df[df["agent-0_identifier"] == "29255f7c-19f0-4fd4-bf63-d3f926ca8915"]
    # df = df[df.max_episode_num >= 20]
    df["agent-0_doc_in_focus"] = (
        df["agent-0_doc_in_focus"].map(lambda x: x if not pd.isna(x) else 0).astype(int)
    )

    df.rename(
        columns={"agent-0_identifier": "mturk_id", "agent-0_reward": "score"},
        inplace=True,
    )
    df = df[
        df.mturk_id.apply(
            lambda x: len(str(x)) in [12, 13, 14, 15] and str(x)[0] == "A"
        )
    ]

    df["score"] = df["score"].map(lambda x: x if x == 1 else 0)

    result = df.groupby("mturk_id").sum(numeric_only=True).reset_index()

    result["proportion_noop"] = result["action_is_noop"] / result["count"]
    result["agent-0_prop_in_focus"] = result["agent-0_doc_in_focus"] / result["count"]

    result.drop(columns=["agent-0_action", "action_is_noop"], inplace=True)

    result["bonus"] = result["score"] * 0.02
    result["bonus"] = result["bonus"].apply(lambda x: min(x, 1.5))
    result.to_csv("data/overcooked_human_ai_bonuses.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
