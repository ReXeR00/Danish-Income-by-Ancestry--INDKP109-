from __future__ import annotations

import pandas as pd


def build_contribution_features(income_long: pd.DataFrame, population_features: pd.DataFrame) -> pd.DataFrame:
    if income_long.empty or population_features.empty or "total_income_thousand_dkk" not in income_long.columns:
        return pd.DataFrame()
    income = income_long.dropna(subset=["total_income_thousand_dkk"]).copy()
    income_totals = (
        income.groupby("year", as_index=False)["total_income_thousand_dkk"]
        .sum()
        .rename(columns={"total_income_thousand_dkk": "all_groups_total_income_thousand_dkk"})
    )
    income = income.merge(income_totals, on="year", how="left")
    income["income_share"] = income["total_income_thousand_dkk"] / income["all_groups_total_income_thousand_dkk"]
    pop = population_features[["year", "group_code", "group_name", "population_share"]]
    out = pop.merge(income[["year", "group_code", "income_share"]], on=["year", "group_code"], how="inner")
    out["contribution_index"] = out["income_share"] / out["population_share"]
    return out.sort_values(["year", "group_code"])
