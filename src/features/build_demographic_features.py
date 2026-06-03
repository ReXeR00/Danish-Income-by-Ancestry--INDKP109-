from __future__ import annotations

import pandas as pd


def build_demographic_driver_features(
    population_features: pd.DataFrame,
    births_long: pd.DataFrame,
    migration_long: pd.DataFrame,
) -> pd.DataFrame:
    if population_features.empty:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    if not births_long.empty:
        births = births_long.copy()
        birth_totals = births.groupby("year", as_index=False)["births"].sum().rename(columns={"births": "total_births"})
        births = births.merge(birth_totals, on="year", how="left")
        births["birth_share"] = births["births"] / births["total_births"]
        mother_map = {
            "DANSK": "DANSK",
            "IMMIGRANT_MOTHER": "IMMIGRANT_BACKGROUND_MOTHER",
            "DESCENDANT_MOTHER": "IMMIGRANT_BACKGROUND_MOTHER",
        }
        births["group_code"] = births["mother_group_code"].map(mother_map)
        births = births.dropna(subset=["group_code"])
        births = births.groupby(["year", "group_code"], as_index=False).agg({"births": "sum", "total_births": "first"})
        births["birth_share"] = births["births"] / births["total_births"]
        frames.append(births)
    if frames:
        demo = frames[0]
    else:
        demo = pd.DataFrame(columns=["year", "group_code"])
    pop = population_features[["year", "group_code", "group_name", "population_share", "population"]].copy()
    immigrant_pop = (
        pop[pop["group_code"].isin(["IND_VEST", "IND_ANDRE"])]
        .groupby("year", as_index=False)
        .agg({"population_share": "sum", "population": "sum"})
    )
    immigrant_pop["group_code"] = "IMMIGRANT_BACKGROUND_MOTHER"
    immigrant_pop["group_name"] = "Immigrant-background mother proxy"
    pop_proxy = pd.concat([pop, immigrant_pop], ignore_index=True)
    out = pop_proxy.merge(demo, on=["year", "group_code"], how="left")
    out["birth_population_ratio"] = out["birth_share"] / out["population_share"]
    if not migration_long.empty:
        mig = migration_long.copy()
        mig["group_code"] = mig["migration_group_code"].map(
            {"DANISH_CITIZENSHIP": "DANSK", "FOREIGN_CITIZENSHIP": "IMMIGRANT_BACKGROUND_MOTHER"}
        )
        mig = mig.groupby(["year", "group_code"], as_index=False).agg(
            immigration_count=("immigration", "sum"),
            emigration_count=("emigration", "sum"),
            net_migration=("net_migration", "sum"),
        )
        out = out.merge(mig, on=["year", "group_code"], how="left")
        out["net_migration_rate"] = out["net_migration"] / out["population"]
    return out.sort_values(["year", "group_code"])
