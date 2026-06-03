from __future__ import annotations

from .eda.hypothesis_01_population_share import create_hypothesis_01_plots
from .eda.hypothesis_02_income_gap import create_hypothesis_02_plots
from .eda.hypothesis_03_relative_income_growth import create_hypothesis_03_plots
from .eda.hypothesis_04_contribution_index import create_hypothesis_04_plots
from .eda.hypothesis_05_births_migration import create_hypothesis_05_plots
from .eda.overview_plots import create_overview_plots
from .pipeline import build_all_datasets
from .tables import write_project_tables


def main() -> None:
    outputs = build_all_datasets()
    write_project_tables(outputs)
    create_hypothesis_01_plots(outputs.population_features, outputs.births_long)
    create_hypothesis_02_plots(outputs.income_features)
    create_hypothesis_03_plots(outputs.income_features)
    create_hypothesis_04_plots(outputs.contribution_features)
    create_hypothesis_05_plots(outputs.births_long, outputs.migration_long, outputs.demographic_features)
    create_overview_plots(outputs.income_features, outputs.population_features, outputs.contribution_features, outputs.demographic_features)
    print("EDA complete. Figures saved under reports/figures/.")


if __name__ == "__main__":
    main()
