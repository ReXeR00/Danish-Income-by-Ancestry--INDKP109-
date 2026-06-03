from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .paths import REPORTS_TABLES
from .pipeline import PipelineOutputs
from .stats.hypothesis_tests import run_contribution_tests, run_income_gap_tests, run_relative_growth_tests


def _write_note(filename: str, text: str) -> None:
    (REPORTS_TABLES / filename).write_text(text.strip() + "\n", encoding="utf-8")


def _gap_forecast(income_features: pd.DataFrame, horizon: int = 10) -> pd.DataFrame:
    gap = income_features[income_features["group_code"] != "DANSK"].dropna(subset=["income_gap_vs_danes"]).copy()
    rows = []
    for group_code, group in gap.groupby("group_code"):
        if len(group) < 2:
            continue
        model = LinearRegression().fit(group[["year"]], group["income_gap_vs_danes"])
        for year in range(int(group["year"].max()) + 1, int(group["year"].max()) + horizon + 1):
            pred = float(model.predict(pd.DataFrame({"year": [year]}))[0])
            rows.append(
                {
                    "year": year,
                    "group_code": group_code,
                    "group_name": group["group_name"].iloc[0],
                    "forecast_income_gap_vs_danes": pred,
                    "note": "Simple linear scenario, not an official forecast.",
                }
            )
    return pd.DataFrame(rows)


def _birth_summary(births_long: pd.DataFrame) -> pd.DataFrame:
    if births_long.empty:
        return pd.DataFrame()
    out = births_long.copy()
    totals = out.groupby("year", as_index=False)["births"].sum().rename(columns={"births": "total_births"})
    out = out.merge(totals, on="year", how="left")
    out["birth_share"] = out["births"] / out["total_births"]
    return out


def write_project_tables(outputs: PipelineOutputs) -> None:
    REPORTS_TABLES.mkdir(parents=True, exist_ok=True)
    for old in [
        "overview_feature_availability.csv",
        "overview_structural_missingness.csv",
        "overview_question_to_output_map.csv",
        "overview_interactive_index.csv",
        "overview_notes_and_limitations.md",
        "hypothesis_01_births_summary.csv",
        "hypothesis_01_model_metrics.csv",
        "hypothesis_01_population_scenarios.csv",
        "hypothesis_01_population_thresholds.csv",
        "hypothesis_03_relative_growth_tests.csv",
        "hypothesis_04_contribution_index.csv",
        "hypothesis_05_births_migration.csv",
    ]:
        path = REPORTS_TABLES / old
        if path.exists():
            path.unlink()

    inventory_rows = []
    for block, table, df, freq, unit, used, note in [
        ("Income", "INDKP109", outputs.income_features, "annual", "DKK/person; thousand DKK", "H2, H3, H4", "INDKP109 currently starts in 2008, but the project income analysis uses 2015 onward from the cache."),
        ("Population", "FOLK1E", outputs.population_features, "annual Q4 snapshot", "people; share", "H1, H4", "FOLK1E ancestry/origin data are available from 2008Q1; no 2000 data are invented."),
        ("Contribution", "INDKP109 + FOLK1E", outputs.contribution_features, "annual", "share; index", "H4", "Requires matching income and population years."),
        ("Births", "FODIE", outputs.births_long, "annual", "live births", "H5", "Births are by mother's background, not child ancestry."),
        ("Migration", "VAN1AAR + VAN2AAR", outputs.migration_long, "annual", "people", "H5", "Citizenship-based proxy."),
        ("CPI / real income", "PRIS111", outputs.cpi, "annual average", "index", "H3", "Used for real-income adjustment."),
    ]:
        if df.empty or "year" not in df.columns:
            first = latest = np.nan
        else:
            first = int(df["year"].min())
            latest = int(df["year"].max())
        inventory_rows.append({"dataset_block": block, "source_table": table, "first_year": first, "latest_year": latest, "frequency": freq, "unit": unit, "used_in_hypotheses": used, "note": note})
    pd.DataFrame(inventory_rows).to_csv(REPORTS_TABLES / "overview_dataset_inventory.csv", index=False)

    snapshot_rows = []
    if not outputs.income_features.empty:
        latest = outputs.income_features[outputs.income_features["year"] == outputs.income_features["year"].max()]
        for _, row in latest.iterrows():
            snapshot_rows.append({"metric": "income_dkk_per_person", "group": row["group_name"], "value": row["income_dkk_per_person"], "unit": "DKK/person", "latest_year": int(row["year"]), "source_table": "INDKP109", "used_in_hypothesis": "H2, H3", "interpretation_note": "Latest complete income year."})
    if not outputs.population_features.empty:
        latest = outputs.population_features[outputs.population_features["year"] == outputs.population_features["year"].max()]
        for _, row in latest.iterrows():
            snapshot_rows.append({"metric": "population_share", "group": row["group_name"], "value": row["population_share"], "unit": "share", "latest_year": int(row["year"]), "source_table": "FOLK1E", "used_in_hypothesis": "H1, H4", "interpretation_note": "Latest available population year."})
    if not outputs.contribution_features.empty:
        latest = outputs.contribution_features[outputs.contribution_features["year"] == outputs.contribution_features["year"].max()]
        for _, row in latest.iterrows():
            snapshot_rows.append({"metric": "contribution_index", "group": row["group_name"], "value": row["contribution_index"], "unit": "index", "latest_year": int(row["year"]), "source_table": "INDKP109 + FOLK1E", "used_in_hypothesis": "H4", "interpretation_note": "1.0 means proportional taxable-income representation."})
    pd.DataFrame(snapshot_rows).to_csv(REPORTS_TABLES / "overview_latest_snapshot.csv", index=False)

    income = outputs.income_features.copy()
    income.to_csv(REPORTS_TABLES / "hypothesis_02_income_features.csv", index=False)
    validation = pd.DataFrame(
        [
            {"check": "income rows", "value": len(outputs.income_long), "note": "Cleaned income records."},
            {"check": "groups", "value": income["group_code"].nunique() if not income.empty else 0, "note": "Expected core groups: DANSK, IND_VEST, IND_ANDRE."},
            {"check": "missing income values", "value": int(income["income_dkk_per_person"].isna().sum()) if not income.empty else np.nan, "note": "Should be zero for core INDKP109 rows."},
        ]
    )
    validation.to_csv(REPORTS_TABLES / "hypothesis_02_income_validation.csv", index=False)
    if not income.empty:
        latest = income[income["year"] == income["year"].max()]
        latest.to_csv(REPORTS_TABLES / "hypothesis_02_latest_year_summary.csv", index=False)
    run_income_gap_tests(income).to_csv(REPORTS_TABLES / "hypothesis_02_income_gap_tests.csv", index=False)
    _gap_forecast(income).to_csv(REPORTS_TABLES / "hypothesis_02_gap_closing_forecast.csv", index=False)
    _write_note("hypothesis_02_notes_and_limitations.md", "Income gaps are descriptive trends from aggregated annual data. They are not causal estimates.")

    income.to_csv(REPORTS_TABLES / "hypothesis_03_growth_features.csv", index=False)
    if not income.empty:
        cumulative = income.sort_values("year").groupby(["group_code", "group_name"], as_index=False).agg(first_income=("income_dkk_per_person", "first"), latest_income=("income_dkk_per_person", "last"), first_real_income=("real_income_dkk_per_person", "first"), latest_real_income=("real_income_dkk_per_person", "last"))
        cumulative["nominal_growth_pct"] = (cumulative["latest_income"] / cumulative["first_income"] - 1) * 100
        cumulative["real_growth_pct"] = (cumulative["latest_real_income"] / cumulative["first_real_income"] - 1) * 100
        cumulative.to_csv(REPORTS_TABLES / "hypothesis_03_cumulative_growth_summary.csv", index=False)
        income.dropna(subset=["yoy_change_pct"]).sort_values("yoy_change_pct", ascending=False).to_csv(REPORTS_TABLES / "hypothesis_03_ranked_yoy_changes.csv", index=False)
        cumulative[["group_code", "group_name", "first_real_income", "latest_real_income", "real_growth_pct"]].to_csv(REPORTS_TABLES / "hypothesis_03_real_income_adjustment.csv", index=False)
    run_relative_growth_tests(income).to_csv(REPORTS_TABLES / "hypothesis_03_growth_tests.csv", index=False)
    _write_note("hypothesis_03_notes_and_limitations.md", "Relative growth uses annual aggregated income. CPI adjustment is included only where CPI data are available.")

    contribution = outputs.contribution_features.copy()
    contribution.to_csv(REPORTS_TABLES / "hypothesis_04_contribution_features.csv", index=False)
    if not contribution.empty:
        latest = contribution[contribution["year"] == contribution["year"].max()].copy()
        latest["gap_from_proportionality"] = latest["contribution_index"] - 1
        latest["income_share_minus_population_share"] = latest["income_share"] - latest["population_share"]
        latest.to_csv(REPORTS_TABLES / "hypothesis_04_latest_summary.csv", index=False)
        latest[["year", "group_code", "group_name", "gap_from_proportionality", "income_share_minus_population_share"]].to_csv(REPORTS_TABLES / "hypothesis_04_gap_from_proportionality.csv", index=False)
    run_contribution_tests(contribution).to_csv(REPORTS_TABLES / "hypothesis_04_trend_tests.csv", index=False)
    _write_note("hypothesis_04_notes_and_limitations.md", "Contribution index compares aggregate taxable-income share with population share. It is descriptive and not causal.")

    births = _birth_summary(outputs.births_long)
    births.to_csv(REPORTS_TABLES / "hypothesis_05_births_summary.csv", index=False)
    demo = outputs.demographic_features.copy()
    if not demo.empty:
        demo[["year", "group_code", "group_name", "population_share", "birth_share", "birth_population_ratio"]].dropna(subset=["birth_population_ratio"]).to_csv(REPORTS_TABLES / "hypothesis_05_birth_population_ratio.csv", index=False)
        gap = demo.copy()
        gap["birth_population_gap"] = gap["birth_share"] - gap["population_share"]
        gap[["year", "group_code", "group_name", "birth_share", "population_share", "birth_population_gap"]].dropna(subset=["birth_population_gap"]).to_csv(REPORTS_TABLES / "hypothesis_05_birth_population_gap.csv", index=False)
    outputs.migration_long.to_csv(REPORTS_TABLES / "hypothesis_05_migration_summary.csv", index=False)
    if not outputs.migration_long.empty:
        outputs.migration_long[["year", "migration_group_code", "migration_group_name", "net_migration"]].to_csv(REPORTS_TABLES / "hypothesis_05_net_migration.csv", index=False)
    _write_note("hypothesis_05_notes_and_limitations.md", "Births are by mother's background. Migration is citizenship-based. Deaths by the same ancestry/origin grouping are not included.")
