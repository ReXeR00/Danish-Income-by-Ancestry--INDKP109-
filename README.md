# Danish Income by Ancestry and Demographic Change

This project uses public Statistics Denmark / StatBank Denmark data to study whether Denmark's demographic change is matched by economic convergence across people of Danish origin, western immigrant origin, and non-western immigrant origin.

Central research question:

> Is Denmark's demographic change matched by economic convergence?

The analysis is exploratory and based on aggregated yearly data. It does not make causal claims about individuals.

## Data Sources

Source: Statistics Denmark - StatBank Denmark.

- `INDKP109`: taxable income by ancestry group.
- `FOLK1E`: population by ancestry/origin group.
- `FODIE`: live births by mother's background.
- `VAN1AAR`: immigration.
- `VAN2AAR`: emigration.
- `PRIS111`: consumer price index.

The project uses the public StatBank API. No API keys, passwords, tokens, or environment variables are required.

## Five Hypotheses

1. **Population share**: How has population composition changed, and what do simple scenario models imply about demographic thresholds?
2. **Income gaps**: Are taxable-income gaps vs Danish origin shrinking, stable, or widening?
3. **Relative income growth**: Which groups have faster indexed and cumulative income growth?
4. **Contribution index**: Is each group's taxable-income share proportional to its population share?
5. **Births and migration context**: How do births by mother's background and citizenship-based migration flows add demographic context?

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Run

Generate datasets, tables, and static figures:

```bash
python -m src.run_eda
```

Run hypothesis tests:

```bash
python -m src.run_hypothesis_tests
```

Run the full pipeline:

```bash
python -m src.run_all
```

Legacy shortcut:

```bash
python main.py
```

## Output Folders

- `data/raw/`: cached StatBank API responses.
- `data/processed/`: cleaned long-format datasets.
- `data/final/`: engineered analytical datasets.
- `reports/figures/overview/`: project overview figures.
- `reports/figures/hypothesis_01_population_share/`: population-share figures.
- `reports/figures/hypothesis_02_income_gap/`: income-gap figures.
- `reports/figures/hypothesis_03_relative_income_growth/`: income-growth figures.
- `reports/figures/hypothesis_04_contribution_index/`: contribution-index figures.
- `reports/figures/hypothesis_05_births_migration/`: births and migration figures.
- `reports/tables/`: summary, feature, test, and notes tables.
- `reports/final_report.md`: compact final report.

## Important Notes


- Births from `FODIE` are grouped by mother's background and should not be read as the child's final ancestry classification.
- Migration features are citizenship-based proxies.
- Deaths by the same ancestry/origin grouping are not included in the current pipeline.
- Scenario forecasts are illustrative, not official predictions.

## Roadmap

- Add validated country-to-origin mappings for births and migration.
- Add compatible labor-market and age-composition controls.
- Add uncertainty bands to scenario forecasts.
- Keep figures and tables compact, readable, and hypothesis-focused.
