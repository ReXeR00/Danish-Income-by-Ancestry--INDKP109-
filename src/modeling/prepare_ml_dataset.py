from __future__ import annotations

import pandas as pd


def prepare_ml_ready_dataset(
    income_features: pd.DataFrame,
    population_features: pd.DataFrame,
    contribution_features: pd.DataFrame,
    demographic_features: pd.DataFrame,
) -> pd.DataFrame:
    if income_features.empty:
        return pd.DataFrame()
    df = income_features.copy()
    if not population_features.empty:
        df = df.merge(
            population_features[
                ["year", "group_code", "population", "population_share", "immigrant_origin_population", "immigrant_origin_share"]
            ],
            on=["year", "group_code"],
            how="left",
        )
    if not contribution_features.empty:
        df = df.merge(
            contribution_features[["year", "group_code", "income_share", "contribution_index"]],
            on=["year", "group_code"],
            how="left",
        )
    if not demographic_features.empty:
        demo_cols = [
            "year",
            "group_code",
            "birth_share",
            "birth_population_ratio",
            "immigration_count",
            "emigration_count",
            "net_migration",
            "net_migration_rate",
        ]
        available = [col for col in demo_cols if col in demographic_features.columns]
        df = df.merge(demographic_features[available], on=["year", "group_code"], how="left")
    return df.sort_values(["year", "group_code"]).reset_index(drop=True)
