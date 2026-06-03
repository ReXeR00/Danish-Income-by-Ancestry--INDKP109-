from __future__ import annotations

import pandas as pd


def build_income_features(income_long: pd.DataFrame, cpi: pd.DataFrame | None = None) -> pd.DataFrame:
    if income_long.empty:
        return pd.DataFrame()
    df = income_long.copy().sort_values(["group_code", "year"])
    dane = df[df["group_code"] == "DANSK"][["year", "income_dkk_per_person"]].rename(
        columns={"income_dkk_per_person": "income_danes"}
    )
    df = df.merge(dane, on="year", how="left")
    df["income_gap_vs_danes"] = df["income_danes"] - df["income_dkk_per_person"]
    df["income_ratio_vs_danes"] = df["income_dkk_per_person"] / df["income_danes"]
    df["yoy_change_dkk"] = df.groupby("group_code")["income_dkk_per_person"].diff()
    df["yoy_change_pct"] = df.groupby("group_code")["income_dkk_per_person"].pct_change() * 100
    df["rolling_3y_mean"] = df.groupby("group_code")["income_dkk_per_person"].transform(
        lambda s: s.rolling(3, min_periods=1).mean()
    )
    base = df.groupby("group_code")["income_dkk_per_person"].transform("first")
    df["base_year_index"] = df["income_dkk_per_person"] / base * 100
    if cpi is not None and not cpi.empty:
        df = df.merge(cpi[["year", "cpi_deflator_to_latest"]], on="year", how="left")
        df["real_income_dkk_per_person"] = df["income_dkk_per_person"] * df["cpi_deflator_to_latest"]
    else:
        df["real_income_dkk_per_person"] = pd.NA
    group_order = {code: idx for idx, code in enumerate(sorted(df["group_code"].dropna().unique()))}
    df["group_encoded"] = df["group_code"].map(group_order)
    cols = [
        "year",
        "group_code",
        "group_name",
        "income_dkk_per_person",
        "total_income_thousand_dkk",
        "income_gap_vs_danes",
        "income_ratio_vs_danes",
        "yoy_change_dkk",
        "yoy_change_pct",
        "rolling_3y_mean",
        "base_year_index",
        "real_income_dkk_per_person",
        "group_encoded",
    ]
    return df[[col for col in cols if col in df.columns]].sort_values(["year", "group_code"])
