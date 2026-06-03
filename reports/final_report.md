# Danish Income by Ancestry and Demographic Change

## 1. Executive summary

This project asks a central descriptive research question: **Is Denmark's demographic change matched by economic convergence?** In practical terms, the analysis compares changes in population composition, births by mother's background, migration flows, taxable income per person, relative income growth, and taxable-income representation across Danish-origin, Western immigrant-origin, and Non-western immigrant-origin groups.

The project uses aggregated public data from Statistics Denmark / StatBank Denmark, including INDKP109 for taxable income, FOLK1E for population by ancestry/origin, FODIE for births by mother's background, VAN1AAR and VAN2AAR for migration by citizenship, and PRIS111 for consumer prices. The analysis is exploratory and descriptive. It does not make causal claims about individuals, families, employment behavior, migration policy, or social outcomes.

The main result is mixed. Denmark's population composition has changed visibly in the available FOLK1E period, and immigrant-origin groups form a larger share of the population than at the start of the series. Economic convergence is more uneven. Western immigrant-origin income per person is close to Danish-origin income in the latest income year, while Non-western immigrant-origin income has grown but remains lower in several indicators. Contribution-index results also show that taxable-income representation is not identical to population representation.

Five headline findings stand out:

1. Population data support a clear composition shift from Danish origin toward immigrant-origin groups in the available 2008-2025 FOLK1E series.
2. Scenario models for population-share thresholds differ substantially, showing that long-run conclusions depend strongly on model assumptions.
3. Western immigrant-origin taxable income per person is near Danish-origin income in the latest income snapshot.
4. Non-western immigrant-origin groups show meaningful relative income growth from the base year, but the latest income ratio remains below Danish origin.
5. Births by mother's background and migration by citizenship add demographic context, but they are proxy measures and do not form a complete natural-change model.

Terminology matters throughout the report. "Immigrant-origin" refers to ancestry/origin groupings where those are the table definitions. Birth data are interpreted as births by mother's background, not the child's final ancestry classification. Migration tables use citizenship-based categories. These definitions limit direct comparability and are one reason the project avoids causal language.

## 2. Data overview

The overview section is a data map rather than a hypothesis test. It explains which datasets are used, which years they cover, which features are available, and where each research question is answered.

Source: Statistics Denmark - StatBank Denmark, accessed 2026-06-01.

Main dataset blocks:

| Dataset block | Source table | Coverage in current outputs | Used for |
| --- | --- | --- | --- |
| Income | INDKP109 | 2008-2024 | Hypotheses 2, 3, and 4 |
| Population | FOLK1E | 2008-2025 | Hypotheses 1 and 4 |
| Contribution | INDKP109 + FOLK1E | 2008-2024 | Hypothesis 4 |
| Births | FODIE | 2007-2025 | Hypothesis 5 |
| Migration | VAN1AAR + VAN2AAR | 2007-2025 | Hypothesis 5 |
| CPI / real income | PRIS111 | 2001-2025 | Hypothesis 3 |
| Combined ML-ready dataset | Engineered merge | 2008-2024 | Cross-hypothesis analytical features |

Key overview outputs:

- Dataset inventory: `reports/tables/overview_dataset_inventory.csv`
- Latest project snapshot: `reports/tables/overview_latest_snapshot.csv`
- Feature availability: `reports/tables/overview_feature_availability.csv`
- Structural missingness: `reports/tables/overview_structural_missingness.csv`
- Research question map: `reports/tables/overview_question_to_output_map.csv`


Important coverage note: the original project ambition includes analysis since 2000, but the currently implemented population table, FOLK1E, starts in 2008Q1. The project does not invent 2000-2007 population values. Hypothesis 1 therefore uses the available 2008-2025 population series unless a compatible earlier StatBank table is added later.

High missingness in the combined analytical dataset is mostly structural. Not every feature is meaningful for every dataset block. For example, birth-share variables apply to the demographic-context block, while income-gap variables apply to the income block.

Static PNG figures are used for the written report. 

## 3. Data cleaning and feature engineering

The project keeps the data pipeline API-based while supporting cached local files. Raw StatBank CSV responses are saved under `data/raw/`, cleaned datasets under `data/processed/`, and engineered analytical datasets under `data/final/`.

Cleaning focuses on making StatBank outputs comparable across tables. Year fields are standardized, group codes are mapped to readable group names, numeric values are converted from StatBank CSV output, and table-specific units are preserved. For income, INDKP109 uses taxable income with DKK per person and, where available, total taxable income in thousand DKK. For population, FOLK1E is treated as a population-by-ancestry/origin source, using annualized snapshots in the current pipeline.

Feature engineering creates the main analytical variables used in the hypotheses:

- Income features: income gap versus Danish origin, income ratio versus Danish origin, year-over-year change, rolling mean, base-year index, and real-income adjustment where CPI is available.
- Population features: population share, immigrant-origin population, and immigrant-origin share.
- Contribution features: income share, population share, contribution index, and difference from proportional representation.
- Demographic-context features: birth share, birth-population ratio, immigration, emigration, net migration, and net migration rate where compatible data are available.

The combined ML-ready dataset merges available features by year and group. Missing values in that file often mean that a feature belongs to a different dataset block, not that the source table failed.

## 4. Hypothesis 1: Population share

Research question: **How has Denmark's population composition changed since the available population series begins, and what do different population-share scenario models imply about future demographic thresholds?**

Data used: FOLK1E population data by ancestry/origin. The current FOLK1E pipeline covers 2008-2025, so this hypothesis does not claim measured 2000-2007 population-share results.

Key figures:

- `reports/figures/hypothesis_01_population_share/01_population_count_over_time.png`
- `reports/figures/hypothesis_01_population_share/02_population_share_over_time.png`
- `reports/figures/hypothesis_01_population_share/03_population_share_100pct_stacked_area.png`
- `reports/figures/hypothesis_01_population_share/05_immigrant_origin_share_with_model_fits.png`
- `reports/figures/hypothesis_01_population_share/06_scenario_threshold_forecast.png`

Key tables:

- `reports/tables/hypothesis_01_population_milestones.csv`
- `reports/tables/hypothesis_01_population_changes.csv`
- `reports/tables/hypothesis_01_threshold_crossing_years.csv`
- `reports/tables/hypothesis_01_model_metrics.csv`

What the result shows: the available population series shows a visible shift in composition, with immigrant-origin groups accounting for a larger share of the population over time and Danish origin accounting for a smaller share. The 100 percent stacked area chart is the clearest summary of that structural change because it compares shares rather than raw counts.

What it suggests: threshold forecasts should be read as scenario illustrations, not official projections. Linear, logarithmic, and logistic models make different assumptions about future change, so their crossing years can diverge substantially.

Limitations: FOLK1E starts in 2008Q1 in the current pipeline. Earlier 2000-2007 population results are not estimated. Long-run thresholds, especially high thresholds, are mathematical scenarios rather than demographic predictions.

## 5. Hypothesis 2: Income gaps

Research question: **Are taxable-income gaps between Danish-origin and immigrant-origin groups shrinking, stable, or widening over time?**

Data used: INDKP109 taxable income per person, 2008-2024.

Key figures:

- `reports/figures/hypothesis_02_income_gap/01_income_per_person_over_time.png`
- `reports/figures/hypothesis_02_income_gap/02_income_gap_vs_danes_over_time.png`
- `reports/figures/hypothesis_02_income_gap/03_income_ratio_vs_danes_over_time.png`
- `reports/figures/hypothesis_02_income_gap/06_income_gap_regression_trend.png`

Key table:

- `reports/tables/hypothesis_02_income_gap_tests.csv`

What the result shows: income gaps are not identical across immigrant-origin groups. In the latest project snapshot, Western immigrant-origin taxable income per person is close to Danish-origin income, while Non-western immigrant-origin income remains lower, with an income ratio of about 0.78 versus Danish origin.

What it suggests: convergence is not a single uniform pattern. The Western immigrant-origin series is closer to Danish origin in the latest income year. The Non-western immigrant-origin series shows improvement in some growth indicators, but the level gap remains an important part of the story.

Limitations: the tests use annual aggregated group-level data. Trend p-values and coefficients describe patterns in these series, not causal effects or individual-level mobility.

## 6. Hypothesis 3: Relative income growth

Research question: **Do immigrant-origin groups experience faster relative taxable-income growth than Danish origin?**

Data used: INDKP109 taxable income per person, with CPI adjustment from PRIS111 where available.

Key figures:

- `reports/figures/hypothesis_03_relative_income_growth/01_base_year_index_over_time.png`
- `reports/figures/hypothesis_03_relative_income_growth/02_yoy_percentage_change_over_time.png`
- `reports/figures/hypothesis_03_relative_income_growth/05_cumulative_growth_barplot.png`
- `reports/figures/hypothesis_03_relative_income_growth/06_yoy_change_heatmap.png`

Key tables:

- `reports/tables/hypothesis_03_relative_growth_tests.csv`
- `reports/tables/hypothesis_03_cumulative_growth_summary.csv`

What the result shows: relative income growth from the base year is stronger for immigrant-origin groups than for Danish origin in the cumulative-growth summary. Non-western immigrant-origin income shows the largest percentage increase from its lower starting level, while Western immigrant-origin income also grows faster than Danish-origin income in indexed terms.

What it suggests: relative growth and income-level convergence are related but not the same. A group can grow faster from a lower base and still remain below another group in the latest income level.

Limitations: annual sample sizes are small, and correlations or growth comparisons can be influenced by inflation, labor-market composition, age structure, and other factors not controlled in this project.

## 7. Hypothesis 4: Contribution index

Research question: **Is each ancestry/origin group's share of total taxable income proportional to its population share?**

Data used: INDKP109 total taxable income and FOLK1E population, aligned to common years.

Key figures:

- `reports/figures/hypothesis_04_contribution_index/01_population_share_vs_income_share_over_time.png`
- `reports/figures/hypothesis_04_contribution_index/02_contribution_index_over_time.png`
- `reports/figures/hypothesis_04_contribution_index/04_latest_contribution_index_barplot.png`
- `reports/figures/hypothesis_04_contribution_index/06_contribution_index_heatmap.png`

Key tables:

- `reports/tables/hypothesis_04_contribution_index.csv`
- `reports/tables/hypothesis_04_latest_summary.csv`

What the result shows: the contribution index summarizes taxable-income representation relative to population share. A value of 1.0 means a group's share of total taxable income equals its population share. In the latest aligned year, Danish origin is above 1.0, Western immigrant origin is below but closer to proportional representation, and Non-western immigrant origin is further below proportional representation.

What it suggests: taxable-income representation is uneven across groups. This is a descriptive income-share measure, not a measure of taxes paid, fiscal contribution, welfare use, or social value.

Limitations: the index does not control for age, employment status, education, family structure, hours worked, or other composition differences that can affect taxable income.

## 8. Hypothesis 5: Births and migration context

Research question: **Do births by mother's background and migration flows by citizenship provide demographic context for changes in population share?**

Data used: FODIE births by mother's background, VAN1AAR immigration, VAN2AAR emigration, and population features where compatible.

Key figures:

- `reports/figures/hypothesis_05_births_migration/01_birth_share_by_mothers_background.png`
- `reports/figures/hypothesis_05_births_migration/02_birth_share_vs_population_share.png`
- `reports/figures/hypothesis_05_births_migration/03_birth_population_ratio.png`
- `reports/figures/hypothesis_05_births_migration/04_immigration_emigration_over_time.png`
- `reports/figures/hypothesis_05_births_migration/05_net_migration_over_time.png`

Key tables:

- `reports/tables/hypothesis_05_births_migration.csv`
- `reports/tables/hypothesis_01_births_summary.csv`

What the result shows: births by mother's background and migration flows add demographic context to the population-share analysis. The latest overview snapshot shows the immigrant-background mother proxy with a birth-population ratio above 1.0 and Danish origin below 1.0, meaning birth share differs from population share in the current proxy comparison.

What it suggests: demographic change is not only about one flow. Birth patterns and migration flows both help explain why population composition may change over time, but the available variables use different definitions.

Limitations: FODIE is interpreted as births by mother's background, not the child's final ancestry classification. Migration data are citizenship-based proxies. Deaths by the same ancestry/origin grouping were not included because a compatible public StatBank table was not available in the current pipeline. Therefore, this section is demographic context, not a complete births-minus-deaths natural-change model and not causal proof.

## 9. Hypothesis testing and significance analysis

The statistical analysis uses simple, transparent methods: trend regressions, group comparisons, cumulative-growth summaries, and scenario-model metrics. These outputs are saved in `reports/tables/` and are intended to support interpretation, not to replace visual inspection.

For Hypothesis 2, income-gap trend tests estimate whether the gap versus Danish origin changes over time for Western and Non-western immigrant-origin groups. For Hypothesis 3, relative-growth tests compare year-over-year and indexed income changes. For Hypothesis 4, contribution-index trends describe whether taxable-income representation moves toward or away from proportionality. For Hypothesis 1, model metrics compare linear, logarithmic, and logistic scenario fits.

The tests should be read cautiously. The data are annual, aggregated, and group-level. Small sample sizes limit statistical power, and statistical significance does not imply causality. Where a model cannot be estimated reliably or a table definition is incompatible, the project records the limitation rather than filling the gap with artificial data.

## 10. Key findings

1. **Population composition has changed in the available FOLK1E series.** Danish origin remains the largest group, but immigrant-origin groups account for a larger population share in the latest population year than at the start of the implemented population series.

2. **Long-run population thresholds are assumption-sensitive.** Linear, logarithmic, and logistic scenarios can imply different crossing years, so the threshold table should be read as a model comparison rather than a prediction.

3. **Western immigrant-origin income is close to Danish-origin income in the latest income snapshot.** The latest overview table reports an income ratio near 1.0 for Western immigrant origin versus Danish origin.

4. **Non-western immigrant-origin income has grown, but the latest level remains lower.** The relative-growth analysis shows stronger percentage growth from a lower base, while the latest income ratio remains below Danish origin.

5. **Taxable-income representation differs from population representation.** The contribution index is above 1.0 for Danish origin in the latest aligned year and below 1.0 for both immigrant-origin groups, with Non-western immigrant origin further below proportional representation.

6. **Births and migration add context but not causal proof.** Births are grouped by mother's background and migration uses citizenship-based categories, so these indicators cannot be treated as a complete demographic mechanism.

7. **The combined analytical dataset is useful, but missingness is often structural.** Many variables exist only for specific dataset blocks, so missing values in the merged file do not automatically indicate poor data quality.

## 11. Limitations

- The analysis is exploratory and descriptive, not causal.
- Population data in the current pipeline use FOLK1E from 2008 onward, even though the broader research motivation refers to change since 2000.
- Aggregated group-level annual data cannot describe individual income mobility or household-level outcomes.
- Group definitions differ across tables: ancestry/origin, mother's background, and citizenship are not interchangeable.
- Births by mother's background are not the same as the child's final ancestry classification.
- Migration data are citizenship-based proxies in the current pipeline.
- Deaths by the same ancestry/origin grouping are not included because a compatible public table was not available in the current pipeline.
- Contribution index measures taxable-income representation relative to population share. It does not measure taxes paid, fiscal balance, public-service use, or broader social contribution.
- Forecasts and thresholds are scenario illustrations and depend strongly on model assumptions.

## 12. Conclusion

The answer to the central question is mixed. Denmark's demographic change is visible in the available population data, and immigrant-origin groups have become a larger share of the population. There is also evidence of some economic convergence, especially in relative income growth and in the latest income level for Western immigrant origin.

However, convergence is partial and uneven. Western immigrant-origin income is close to Danish-origin income in the latest snapshot, while Non-western immigrant-origin income has improved from its base year but remains below Danish origin in income ratio and taxable-income representation. The contribution-index analysis reinforces that demographic presence and taxable-income representation are not yet proportional for all groups.

Overall, the project supports a careful conclusion: Denmark's demographic composition has changed, and some economic indicators show movement toward convergence, but the convergence is incomplete, group-specific, and descriptive rather than causal.

## 13. Next steps

1. Add country-to-origin mapping where StatBank tables use country or citizenship categories rather than ancestry/origin categories.
2. Extend the analysis with age, employment, education, and labor-force participation controls where compatible public data are available.
3. Add uncertainty bands for scenario forecasts and clearly separate observed data from extrapolated values.
4. Validate all table selections and dimension mappings against the relevant StatBank metadata before publication.
5. Keep the project compact and focused so the final portfolio version remains readable, reproducible, and easy to navigate.
