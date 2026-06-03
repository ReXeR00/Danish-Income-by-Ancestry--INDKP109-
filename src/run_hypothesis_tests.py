from __future__ import annotations

from .paths import REPORTS_TABLES, ensure_project_dirs
from .pipeline import build_all_datasets, load_final_datasets
from .stats.hypothesis_tests import run_contribution_tests, run_income_gap_tests, run_relative_growth_tests


def main() -> None:
    ensure_project_dirs()
    datasets = load_final_datasets()
    if datasets["income_features"].empty:
        print("Final datasets not found; building them first.")
        outputs = build_all_datasets()
        datasets = {
            "income_features": outputs.income_features,
            "population_features": outputs.population_features,
            "contribution_features": outputs.contribution_features,
            "demographic_features": outputs.demographic_features,
        }
    results = {
        "hypothesis_02_income_gap_tests": run_income_gap_tests(datasets["income_features"]),
        "hypothesis_03_growth_tests": run_relative_growth_tests(datasets["income_features"]),
        "hypothesis_04_trend_tests": run_contribution_tests(datasets["contribution_features"]),
    }
    for name, df in results.items():
        if df is not None and not df.empty:
            df.to_csv(REPORTS_TABLES / f"{name}.csv", index=False)
            print(f"Saved {name}.csv ({len(df):,} rows)")
        else:
            print(f"Skipped {name}: no data")


if __name__ == "__main__":
    main()
