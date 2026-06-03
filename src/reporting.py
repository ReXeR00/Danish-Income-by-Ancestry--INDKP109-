from __future__ import annotations

from datetime import date

import pandas as pd

from .paths import REPORTS, REPORTS_TABLES, ensure_project_dirs


def _inventory_lines() -> str:
    path = REPORTS_TABLES / "overview_dataset_inventory.csv"
    if not path.exists():
        return "- Dataset inventory has not been generated yet."
    df = pd.read_csv(path)
    lines = []
    for _, row in df.iterrows():
        first = int(row["first_year"]) if pd.notna(row["first_year"]) else "not loaded"
        latest = int(row["latest_year"]) if pd.notna(row["latest_year"]) else "not loaded"
        lines.append(f"- {row['dataset_block']}: `{row['source_table']}`, {first}-{latest}, used in {row['used_in_hypotheses']}.")
    return "\n".join(lines)


def write_final_report() -> None:
    ensure_project_dirs()
    accessed = date.today().isoformat()
    text = f"""# Danish Income by Ancestry and Demographic Change

## 1. Executive summary

This project asks whether Denmark's demographic change is matched by economic convergence. It uses public Statistics Denmark / StatBank Denmark data to compare population composition, taxable income per person, contribution to aggregate taxable income, births by mother's background, and citizenship-based migration flows.

The analysis is descriptive and exploratory. It uses aggregated annual group-level data and does not make causal claims about individuals.

## 2. Data overview

Source: Statistics Denmark - StatBank Denmark, accessed {accessed}.

{_inventory_lines()}

Key overview outputs:

- `reports/figures/overview/01_dataset_coverage_timeline.png`
- `reports/figures/overview/02_feature_availability_matrix.png`
- `reports/figures/overview/03_latest_project_snapshot_dashboard.png`
- `reports/tables/overview_dataset_inventory.csv`
- `reports/tables/overview_latest_snapshot.csv`

Important coverage note: FOLK1E ancestry/origin population data start in 2008Q1. If no compatible population table with the same grouping is available from 2000, the population-share analysis uses 2008 onward and labels the first milestone as the nearest available year.

## 3. Hypothesis 1: Population share

Research question: How has Denmark's population composition changed, and what do simple population-share scenarios imply about future thresholds?

Data used: `FOLK1E` population by ancestry/origin grouping.

Key figures:

- `reports/figures/hypothesis_01_population_share/01_population_count_over_time.png`
- `reports/figures/hypothesis_01_population_share/02_population_share_over_time.png`
- `reports/figures/hypothesis_01_population_share/03_population_share_100pct_stacked_area.png`
- `reports/figures/hypothesis_01_population_share/04_population_milestone_comparison.png`
- `reports/figures/hypothesis_01_population_share/05_scenario_threshold_forecast.png`

Key tables:

- `reports/tables/hypothesis_01_population_milestones.csv`
- `reports/tables/hypothesis_01_population_changes.csv`
- `reports/tables/hypothesis_01_threshold_crossing_years.csv`

What the result shows: The section documents observed population composition and scenario threshold years. Forecast lines are illustrative extrapolations, not official predictions.

Limitations: No 2000 FOLK1E ancestry/origin data are available in the current pipeline. Births and migration are intentionally handled in Hypothesis 5, not in Hypothesis 1.

## 4. Hypothesis 2: Income gaps

Research question: Are taxable-income gaps between Danish-origin and immigrant-origin groups shrinking, stable, or widening?

Data used: `INDKP109`, taxable income, DKK per person.

Key figures:

- `reports/figures/hypothesis_02_income_gap/01_income_per_person_over_time.png`
- `reports/figures/hypothesis_02_income_gap/02_income_ratio_vs_danish_origin.png`
- `reports/figures/hypothesis_02_income_gap/03_income_gap_vs_danish_origin.png`
- `reports/figures/hypothesis_02_income_gap/04_latest_year_income_comparison.png`
- `reports/figures/hypothesis_02_income_gap/05_gap_closing_forecast_next_10_years.png`

Key tables:

- `reports/tables/hypothesis_02_latest_year_summary.csv`
- `reports/tables/hypothesis_02_income_gap_tests.csv`
- `reports/tables/hypothesis_02_gap_closing_forecast.csv`

What the result shows: The section compares income levels, ratios, gaps, and simple gap-closing scenarios.

Limitations: Income gaps are aggregate descriptive differences. They are not causal estimates.

## 5. Hypothesis 3: Relative income growth

Research question: Do immigrant-origin groups experience faster relative taxable-income growth than Danish-origin groups?

Data used: `INDKP109`; `PRIS111` CPI where available.

Key figures:

- `reports/figures/hypothesis_03_relative_income_growth/01_base_year_income_index.png`
- `reports/figures/hypothesis_03_relative_income_growth/02_yoy_percentage_change.png`
- `reports/figures/hypothesis_03_relative_income_growth/03_ranked_yoy_income_changes.png`
- `reports/figures/hypothesis_03_relative_income_growth/04_cumulative_growth_barplot.png`
- `reports/figures/hypothesis_03_relative_income_growth/05_nominal_vs_real_cumulative_growth.png`

Key tables:

- `reports/tables/hypothesis_03_cumulative_growth_summary.csv`
- `reports/tables/hypothesis_03_ranked_yoy_changes.csv`
- `reports/tables/hypothesis_03_growth_tests.csv`
- `reports/tables/hypothesis_03_real_income_adjustment.csv`

What the result shows: The section compares indexed growth, annual changes, cumulative nominal growth, and CPI-adjusted growth where possible.

Limitations: Annual group-level observations are few, so statistical power is limited.

## 6. Hypothesis 4: Contribution index

Research question: Do immigrant-origin groups contribute to total taxable income proportionally to their population share?

Data used: `INDKP109` total taxable income and `FOLK1E` population.

Key figures:

- `reports/figures/hypothesis_04_contribution_index/01_contribution_index_over_time.png`
- `reports/figures/hypothesis_04_contribution_index/02_latest_contribution_index.png`
- `reports/figures/hypothesis_04_contribution_index/03_latest_gap_from_proportionality.png`
- `reports/figures/hypothesis_04_contribution_index/04_income_share_minus_population_share.png`
- `reports/figures/hypothesis_04_contribution_index/05_contribution_index_heatmap.png`

Key tables:

- `reports/tables/hypothesis_04_contribution_features.csv`
- `reports/tables/hypothesis_04_latest_summary.csv`
- `reports/tables/hypothesis_04_trend_tests.csv`
- `reports/tables/hypothesis_04_gap_from_proportionality.csv`

What the result shows: The contribution index compares income share with population share. A value of 1.0 means proportional representation.

Limitations: The index is descriptive and does not explain mechanisms.

## 7. Hypothesis 5: Births and migration context

Research question: Are demographic changes connected with births by mother's background and migration flows?

Data used: `FODIE`, `VAN1AAR`, `VAN2AAR`, and population features where available.

Key figures:

- `reports/figures/hypothesis_05_births_migration/01_birth_share_by_mothers_background.png`
- `reports/figures/hypothesis_05_births_migration/02_birth_population_ratio.png`
- `reports/figures/hypothesis_05_births_migration/03_birth_population_gap.png`
- `reports/figures/hypothesis_05_births_migration/04_net_migration_by_citizenship.png`
- `reports/figures/hypothesis_05_births_migration/05_latest_demographic_driver_snapshot.png`

Key tables:

- `reports/tables/hypothesis_05_births_summary.csv`
- `reports/tables/hypothesis_05_birth_population_ratio.csv`
- `reports/tables/hypothesis_05_birth_population_gap.csv`
- `reports/tables/hypothesis_05_migration_summary.csv`
- `reports/tables/hypothesis_05_net_migration.csv`

What the result shows: The section gives demographic context using births by mother's background and citizenship-based migration flows.

Limitations: Birth data describe mother's background, not the child's final ancestry classification. Migration features are citizenship-based proxies. Deaths by the same ancestry/origin grouping are not included.

## 8. Key findings

The project produces a compact set of tables and static figures for each hypothesis. The strongest interpretation comes from reading the population, income-gap, growth, contribution, and demographic-context sections together.

## 9. Limitations

- Aggregated annual data cannot prove individual-level causality.
- Some tables have different publication horizons.
- FOLK1E starts after 2000 for the required ancestry/origin grouping.
- Birth and migration definitions do not exactly match income ancestry categories.
- Scenario forecasts are illustrative.

## 10. Next steps

- Add a validated country-to-origin mapping for births and migration.
- Add age-composition and employment controls if compatible StatBank tables are available.
- Add uncertainty bands for scenario thresholds.
- Keep outputs compact and focused on the five hypotheses.
"""
    (REPORTS / "final_report.md").write_text(text, encoding="utf-8")
    print("Saved reports/final_report.md")
