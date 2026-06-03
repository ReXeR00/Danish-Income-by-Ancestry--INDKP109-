from __future__ import annotations

from datetime import date

import pandas as pd

from .cache import load_or_fetch
from .statbank_client import available_years, post_statbank_csv


def latest_complete_migration_year() -> int:
    years = available_years("VAN1AAR")
    fallback = date.today().year - 1
    return min(max(years), fallback) if years else fallback


def load_immigration_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    available = available_years("VAN1AAR")
    end_year = end_year or latest_complete_migration_year()
    years_int = [year for year in available if start_year <= year <= end_year]
    if not years_int:
        years_int = [year for year in range(start_year, end_year + 1)]
    years = [str(year) for year in years_int]
    filename = f"van1aar_immigration_{min(years_int)}_{max(years_int)}.csv"
    variables = {
        "OMRÅDE": ["000"],
        "KØN": ["*"],
        "ALDER": ["*"],
        "INDVLAND": ["*"],
        "STATSB": ["*"],
        "Tid": years,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("VAN1AAR", variables, file_format="BULK", timeout=180),
        prefer_cache=prefer_cache,
    )


def load_emigration_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    available = available_years("VAN2AAR")
    end_year = end_year or latest_complete_migration_year()
    years_int = [year for year in available if start_year <= year <= end_year]
    if not years_int:
        years_int = [year for year in range(start_year, end_year + 1)]
    years = [str(year) for year in years_int]
    filename = f"van2aar_emigration_{min(years_int)}_{max(years_int)}.csv"
    variables = {
        "OMRÅDE": ["000"],
        "KØN": ["*"],
        "ALDER": ["*"],
        "UDVLAND": ["*"],
        "STATSB": ["*"],
        "Tid": years,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("VAN2AAR", variables, file_format="BULK", timeout=180),
        prefer_cache=prefer_cache,
    )
