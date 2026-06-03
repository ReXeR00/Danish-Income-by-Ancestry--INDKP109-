from __future__ import annotations

from datetime import date

import pandas as pd

from .cache import load_or_fetch
from .statbank_client import available_years, post_statbank_csv


def latest_complete_birth_year() -> int:
    years = available_years("FODIE")
    fallback = date.today().year - 1
    return min(max(years), fallback) if years else fallback


def load_births_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    available = available_years("FODIE")
    end_year = end_year or latest_complete_birth_year()
    years_int = [year for year in available if start_year <= year <= end_year]
    if not years_int:
        years_int = [year for year in range(start_year, end_year + 1)]
    years = [str(year) for year in years_int]
    filename = f"fodie_births_{min(years_int)}_{max(years_int)}.csv"
    variables = {
        "OMRÅDE": ["000"],
        "MOHERK": ["5", "4", "3", "0"],
        "MOOPRIND": ["*"],
        "MOSTAT": ["*"],
        "MODERSALDER": ["*"],
        "BARNKON": ["*"],
        "Tid": years,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("FODIE", variables, file_format="BULK", timeout=120),
        prefer_cache=prefer_cache,
    )
