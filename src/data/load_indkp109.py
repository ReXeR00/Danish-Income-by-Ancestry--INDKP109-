from __future__ import annotations

from datetime import date

import pandas as pd

from .cache import load_or_fetch
from .statbank_client import available_years, post_statbank_csv


def latest_complete_income_year() -> int:
    years = available_years("INDKP109")
    fallback = date.today().year - 1
    return min(max(years), fallback) if years else fallback


def load_indkp109_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    available = available_years("INDKP109")
    end_year = end_year or latest_complete_income_year()
    years_int = [year for year in available if start_year <= year <= end_year]
    if not years_int:
        years_int = [year for year in range(start_year, end_year + 1)]
    years = [str(year) for year in years_int]
    filename = f"indkp109_income_{min(years_int)}_{max(years_int)}.csv"
    variables = {
        "REGLAND": ["000"],
        "ENHED": ["121", "110"],
        "KOEN": ["MOK"],
        "ALDER1": ["TOT"],
        "HERKOMST": ["DANSK", "IND_VEST", "IND_ANDRE"],
        "INDKOMSTTYPE": ["105"],
        "Tid": years,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("INDKP109", variables, timeout=60),
        prefer_cache=prefer_cache,
    )
