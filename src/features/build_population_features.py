from __future__ import annotations

import pandas as pd


def build_population_features(population_long: pd.DataFrame) -> pd.DataFrame:
    if population_long.empty:
        return pd.DataFrame()
    df = population_long.copy()
    totals = df.groupby("year", as_index=False)["population"].sum().rename(columns={"population": "total_population"})
    df = df.merge(totals, on="year", how="left")
    df["population_share"] = df["population"] / df["total_population"]
    immigrant = (
        df[df["group_code"].isin(["IND_VEST", "IND_ANDRE"])]
        .groupby("year", as_index=False)["population"]
        .sum()
        .rename(columns={"population": "immigrant_origin_population"})
    )
    df = df.merge(immigrant, on="year", how="left")
    df["immigrant_origin_share"] = df["immigrant_origin_population"] / df["total_population"]
    return df.sort_values(["year", "group_code"])
