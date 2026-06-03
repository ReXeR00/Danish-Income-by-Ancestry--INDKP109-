from __future__ import annotations

import traceback
from dataclasses import dataclass

import pandas as pd

from .cleaning.clean_statbank import clean_births_long, clean_cpi_annual, clean_income_long, clean_migration_long, clean_population_long
from .data.load_births import load_births_raw
from .data.load_cpi import load_cpi_raw
from .data.load_indkp109 import load_indkp109_raw
from .data.load_migration import load_emigration_raw, load_immigration_raw
from .data.load_population import load_population_raw
from .features.build_contribution_features import build_contribution_features
from .features.build_demographic_features import build_demographic_driver_features
from .features.build_income_features import build_income_features
from .features.build_population_features import build_population_features
from .modeling.prepare_ml_dataset import prepare_ml_ready_dataset
from .paths import DATA_FINAL, DATA_PROCESSED, ensure_project_dirs


@dataclass
class PipelineOutputs:
    income_long: pd.DataFrame
    population_long: pd.DataFrame
    births_long: pd.DataFrame
    migration_long: pd.DataFrame
    cpi: pd.DataFrame
    income_features: pd.DataFrame
    population_features: pd.DataFrame
    contribution_features: pd.DataFrame
    demographic_features: pd.DataFrame
    ml_ready: pd.DataFrame
    warnings: list[str]


def _safe_load(label: str, loader, warnings: list[str]) -> pd.DataFrame:
    try:
        return loader()
    except Exception as exc:
        warnings.append(f"{label} skipped: {exc}")
        return pd.DataFrame()


def build_all_datasets(start_year: int = 2000, prefer_cache: bool = True, verbose: bool = True) -> PipelineOutputs:
    ensure_project_dirs()
    warnings: list[str] = []
    raw_income = _safe_load("INDKP109 income", lambda: load_indkp109_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)
    raw_population = _safe_load("FOLK1E population", lambda: load_population_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)
    raw_cpi = _safe_load("PRIS111 CPI", lambda: load_cpi_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)
    raw_births = _safe_load("FODIE births", lambda: load_births_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)
    raw_immigration = _safe_load("VAN1AAR immigration", lambda: load_immigration_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)
    raw_emigration = _safe_load("VAN2AAR emigration", lambda: load_emigration_raw(start_year=start_year, prefer_cache=prefer_cache), warnings)

    income_long = clean_income_long(raw_income)
    population_long = clean_population_long(raw_population)
    births_long = clean_births_long(raw_births)
    migration_long = clean_migration_long(raw_immigration, raw_emigration)
    cpi = clean_cpi_annual(raw_cpi)

    income_features = build_income_features(income_long, cpi)
    population_features = build_population_features(population_long)
    contribution_features = build_contribution_features(income_long, population_features)
    demographic_features = build_demographic_driver_features(population_features, births_long, migration_long)
    ml_ready = prepare_ml_ready_dataset(income_features, population_features, contribution_features, demographic_features)

    processed = {
        "income_long.csv": income_long,
        "population_long.csv": population_long,
        "births_long.csv": births_long,
        "migration_long.csv": migration_long,
        "cpi_annual.csv": cpi,
    }
    final = {
        "income_features.csv": income_features,
        "population_features.csv": population_features,
        "contribution_features.csv": contribution_features,
        "demographic_driver_features.csv": demographic_features,
        "ml_ready_denmark_income_demography.csv": ml_ready,
    }
    for filename, df in processed.items():
        if not df.empty:
            df.to_csv(DATA_PROCESSED / filename, index=False)
    for filename, df in final.items():
        if not df.empty:
            df.to_csv(DATA_FINAL / filename, index=False)
    if verbose:
        print("Dataset build summary")
        for name, df in {**processed, **final}.items():
            print(f"- {name}: {len(df):,} rows")
        for warning in warnings:
            safe_warning = str(warning).encode("ascii", errors="replace").decode("ascii")
            print(f"WARNING: {safe_warning}")
    return PipelineOutputs(
        income_long,
        population_long,
        births_long,
        migration_long,
        cpi,
        income_features,
        population_features,
        contribution_features,
        demographic_features,
        ml_ready,
        warnings,
    )


def load_final_datasets() -> dict[str, pd.DataFrame]:
    ensure_project_dirs()
    paths = {
        "income_features": DATA_FINAL / "income_features.csv",
        "population_features": DATA_FINAL / "population_features.csv",
        "contribution_features": DATA_FINAL / "contribution_features.csv",
        "demographic_features": DATA_FINAL / "demographic_driver_features.csv",
        "births_long": DATA_PROCESSED / "births_long.csv",
        "migration_long": DATA_PROCESSED / "migration_long.csv",
    }
    return {name: pd.read_csv(path) if path.exists() else pd.DataFrame() for name, path in paths.items()}
