from __future__ import annotations

from datetime import date

import pandas as pd

from .cache import load_or_fetch
from .statbank_client import available_years, post_statbank_csv


def latest_complete_population_year() -> int:
    years = available_years("FOLK1E")
    fallback = date.today().year - 1
    return min(max(years), fallback) if years else fallback


def load_population_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    available = available_years("FOLK1E")
    end_year = end_year or latest_complete_population_year()
    years = [year for year in available if start_year <= year <= end_year]
    if not years:
        years = [year for year in range(start_year, end_year + 1)]
    quarters = [f"{year}K4" for year in years]
    filename = f"folk1e_population_q4_{min(years)}_{max(years)}.csv"
    variables = {
        "OMRÅDE": ["000"],
        "KØN": ["TOT"],
        "ALDER": ["IALT"],
        "HERKOMST": ["1", "24", "25", "34", "35"],
        "Tid": quarters,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("FOLK1E", variables, timeout=60),
        prefer_cache=prefer_cache,
    )
