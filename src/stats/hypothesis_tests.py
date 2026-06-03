from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

try:
    import statsmodels.formula.api as smf
except ModuleNotFoundError:
    smf = None

from .scenario_forecasts import population_share_scenarios


def _regression_result(df: pd.DataFrame, formula: str, label: str) -> dict[str, object]:
    clean = df.dropna()
    if len(clean) < 3:
        return {"test": label, "status": "not enough observations"}
    if smf is None:
        if "~" in formula and all(token not in formula for token in ["*", "+", "C("]):
            y_col, x_col = [part.strip() for part in formula.split("~", 1)]
            if y_col in clean.columns and x_col in clean.columns:
                x = pd.to_numeric(clean[x_col], errors="coerce").astype(float)
                y = pd.to_numeric(clean[y_col], errors="coerce").astype(float)
                mask = x.notna() & y.notna()
                result = stats.linregress(x[mask].to_numpy(), y[mask].to_numpy())
                return {
                    "rows": [
                        {
                            "test": label,
                            "term": x_col,
                            "coefficient": result.slope,
                            "p_value": result.pvalue,
                            "r_squared": result.rvalue**2,
                            "n_obs": len(clean),
                            "status": "ok scipy fallback",
                        }
                    ]
                }
        return {"test": label, "status": "statsmodels is not installed; install requirements.txt for formula regression"}
    try:
        model = smf.ols(formula, data=clean).fit()
    except Exception as exc:
        return {"test": label, "status": f"failed: {exc}"}
    rows = []
    for param, coef in model.params.items():
        rows.append(
            {
                "test": label,
                "term": param,
                "coefficient": coef,
                "p_value": model.pvalues.get(param),
                "r_squared": model.rsquared,
                "n_obs": int(model.nobs),
                "status": "ok",
            }
        )
    return {"rows": rows}


def run_income_gap_tests(income_features: pd.DataFrame) -> pd.DataFrame:
    if income_features.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for group in ["IND_VEST", "IND_ANDRE"]:
        data = income_features[income_features["group_code"] == group][["year", "income_gap_vs_danes"]].dropna()
        result = _regression_result(data, "income_gap_vs_danes ~ year", f"income gap trend: {group}")
        rows.extend(result.get("rows", [result]))
    interaction = income_features[["year", "group_code", "income_dkk_per_person"]].dropna()
    result = _regression_result(interaction, "income_dkk_per_person ~ year * C(group_code)", "income level interaction")
    rows.extend(result.get("rows", [result]))
    return pd.DataFrame(rows)


def run_relative_growth_tests(income_features: pd.DataFrame) -> pd.DataFrame:
    if income_features.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    samples = [
        group["yoy_change_pct"].dropna().to_numpy()
        for _, group in income_features.groupby("group_code")
        if group["yoy_change_pct"].dropna().shape[0] >= 2
    ]
    if len(samples) >= 2:
        stat, p_value = stats.kruskal(*samples)
        rows.append({"test": "Kruskal-Wallis YoY percentage growth", "statistic": stat, "p_value": p_value, "status": "ok"})
    else:
        rows.append({"test": "Kruskal-Wallis YoY percentage growth", "status": "not enough observations"})
    interaction = income_features[["year", "group_code", "base_year_index"]].dropna()
    result = _regression_result(interaction, "base_year_index ~ year * C(group_code)", "base-year index interaction")
    rows.extend(result.get("rows", [result]))
    first_last = income_features.sort_values("year").groupby("group_code").agg(
        group_name=("group_name", "first"),
        first_year=("year", "first"),
        latest_year=("year", "last"),
        first_income=("income_dkk_per_person", "first"),
        latest_income=("income_dkk_per_person", "last"),
    )
    first_last["cumulative_growth_pct"] = (first_last["latest_income"] / first_last["first_income"] - 1) * 100
    for group_code, row in first_last.reset_index().iterrows():
        rows.append({"test": "cumulative growth", **row.to_dict(), "status": "ok"})
    return pd.DataFrame(rows)


def run_contribution_tests(contribution_features: pd.DataFrame) -> pd.DataFrame:
    if contribution_features.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for group, data in contribution_features.groupby("group_code"):
        result = _regression_result(data[["year", "contribution_index"]], "contribution_index ~ year", f"contribution index trend: {group}")
        rows.extend(result.get("rows", [result]))
    latest_year = contribution_features["year"].max()
    latest = contribution_features[contribution_features["year"] == latest_year]
    for _, row in latest.iterrows():
        rows.append(
            {
                "test": "latest contribution index vs proportional benchmark",
                "group_code": row["group_code"],
                "group_name": row["group_name"],
                "year": latest_year,
                "contribution_index": row["contribution_index"],
                "difference_from_1": row["contribution_index"] - 1,
                "status": "descriptive",
            }
        )
    return pd.DataFrame(rows)


def run_demographic_driver_tests(demo_features: pd.DataFrame) -> pd.DataFrame:
    if demo_features.empty:
        return pd.DataFrame([{"test": "demographic driver model", "status": "missing demographic driver features"}])
    df = demo_features.copy().sort_values(["group_code", "year"])
    df["next_year_population_share"] = df.groupby("group_code")["population_share"].shift(-1)
    rows: list[dict[str, object]] = []
    model_a = _regression_result(df[["year", "next_year_population_share"]], "next_year_population_share ~ year", "Model A: next share from year")
    rows.extend(model_a.get("rows", [model_a]))
    cols = ["next_year_population_share", "population_share", "birth_share", "net_migration_rate"]
    if set(cols).issubset(df.columns):
        model_b = _regression_result(df[cols], "next_year_population_share ~ population_share + birth_share + net_migration_rate", "Model B: births and net migration")
        rows.extend(model_b.get("rows", [model_b]))
    else:
        rows.append({"test": "Model B: births and net migration", "status": "missing birth or migration variables"})
    return pd.DataFrame(rows)


def run_all_hypothesis_tests(
    income_features: pd.DataFrame,
    population_features: pd.DataFrame,
    contribution_features: pd.DataFrame,
    demo_features: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    scenarios, thresholds = population_share_scenarios(population_features)
    return {
        "hypothesis_01_population_thresholds": thresholds,
        "hypothesis_01_population_scenarios": scenarios,
        "hypothesis_02_income_gap_tests": run_income_gap_tests(income_features),
        "hypothesis_03_relative_growth_tests": run_relative_growth_tests(income_features),
        "hypothesis_04_contribution_index": run_contribution_tests(contribution_features),
        "hypothesis_05_births_migration": run_demographic_driver_tests(demo_features),
    }
