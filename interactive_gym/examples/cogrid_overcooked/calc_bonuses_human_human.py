import os

import pandas as pd

DATA_PATH = "data/overcooked/"


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
            "agent-0_identifier",
            "agent-1_identifier",
            "agent-1_is_human",
            "agent-0_reward",
            "agent-0_action",
            "agent-1_action",
        ]
    ]
    df["count"] = 1
    df["action_is_noop"] = df["agent-0_action"] == 6.0
    df = df[df["agent-1_is_human"] == True]

    df.rename(
        columns={
            "agent-0_identifier": "mturk_id_player_0",
            "agent-1_identifier": "mturk_id_player_1",
            "agent-0_reward": "score",
        },
        inplace=True,
    )

    result = (
        df.groupby(["mturk_id_player_0", "mturk_id_player_1"])
        .sum(numeric_only=True)
        .reset_index()
    )

    ids_to_keep = ["A2YM60MOXE9UMF", "AZTYIBLLB60V8", "AN45KLUESX3NY"]
    result = result[
        result["count"]
        >= 19999
        | result["mturk_id_player_0"].isin(ids_to_keep)
        | result["mturk_id_player_1"].isin(ids_to_keep)
    ]
    result["proportion_noop"] = result["action_is_noop"] / result["count"]

    result.drop(columns=["agent-0_action", "action_is_noop"], inplace=True)

    result["bonus"] = result["score"] * 0.02
    result["bonus"] = result["bonus"].apply(lambda x: min(x, 1.5))
    result.to_csv("data/overcooked_human_human_bonuses.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
