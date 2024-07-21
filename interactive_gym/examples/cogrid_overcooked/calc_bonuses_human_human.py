import os

import pandas as pd

DATA_PATH = "data/overcooked/human_human/overcooked"


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
            "agent-0_doc_in_focus",
            "agent-1_doc_in_focus",
        ]
    ]
    df["count"] = 1
    df["player_0_action_is_noop"] = df["agent-0_action"] == 6.0
    df["player_1_action_is_noop"] = df["agent-1_action"] == 6.0
    df["agent-0_doc_in_focus"] = (
        df["agent-0_doc_in_focus"].map(lambda x: x if not pd.isna(x) else 0).astype(int)
    )
    df["agent-1_doc_in_focus"] = (
        df["agent-1_doc_in_focus"].map(lambda x: x if not pd.isna(x) else 0).astype(int)
    )

    # df = df[df["agent-1_is_human"] == True]

    df.rename(
        columns={
            "agent-0_identifier": "mturk_id_player_0",
            "agent-1_identifier": "mturk_id_player_1",
            "agent-0_reward": "score",
        },
        inplace=True,
    )

    df = df[
        df.mturk_id_player_0.apply(
            lambda x: len(str(x)) in [12, 13, 14, 15] and str(x)[0] == "A"
        )
    ]

    result = (
        df.groupby(["mturk_id_player_0", "mturk_id_player_1"])
        .sum(numeric_only=True)
        .reset_index()
    )

    # ids_to_keep = ["A2YM60MOXE9UMF", "AZTYIBLLB60V8", "AN45KLUESX3NY"]
    # result = result[
    #     result["count"]
    #     >= 19999
    #     | result["mturk_id_player_0"].isin(ids_to_keep)
    #     | result["mturk_id_player_1"].isin(ids_to_keep)
    # ]

    result["player_0_proportion_noop"] = (
        result["player_0_action_is_noop"] / result["count"]
    )
    result["player_1_proportion_noop"] = (
        result["player_1_action_is_noop"] / result["count"]
    )
    result["player_0_prop_in_focus"] = result["agent-0_doc_in_focus"] / result["count"]
    result["player_1_prop_in_focus"] = result["agent-1_doc_in_focus"] / result["count"]

    result.drop(
        columns=[
            "agent-0_action",
            "agent-1_action",
            "player_0_action_is_noop",
            "player_1_action_is_noop",
            "agent-0_doc_in_focus",
            "agent-1_doc_in_focus",
        ],
        inplace=True,
    )

    result["count"] /= 1000
    result["bonus"] = result["score"] * 0.02
    result["bonus"] = result["bonus"].apply(lambda x: min(x, 1.5))
    result.to_csv("data/overcooked_human_human_bonuses_0315.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
