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
    df = df[["agent-0_identifier", "agent-0_reward"]]
    df["count"] = 1
    df = df.groupby(["agent-0_identifier"]).sum()

    df = df[df["count"] == 20000]

    df["agent-0_reward"] = df["agent-0_reward"]
    df["bonus"] = df["agent-0_reward"] * 0.02
    df.to_csv("data/overcooked/bonuses_total.csv")


if __name__ == "__main__":
    df = read_files(DATA_PATH)
    calc_bonuses(df)
