from __future__ import annotations

import pandas as pd

from .cache import load_or_fetch
from .statbank_client import available_years, post_statbank_csv


def load_cpi_raw(start_year: int = 2015, end_year: int | None = None, prefer_cache: bool = True) -> pd.DataFrame:
    end_year = end_year or pd.Timestamp.today().year - 1
    available = available_years("PRIS111")
    years = [year for year in available if start_year <= year <= end_year]
    if not years:
        years = [year for year in range(start_year, end_year + 1)]
    months = [f"{year}M{month:02d}" for year in years for month in range(1, 13)]
    filename = f"pris111_cpi_{min(years)}_{max(years)}.csv"
    variables = {
        "VAREGR": ["000000"],
        "ENHED": ["100"],
        "Tid": months,
    }
    return load_or_fetch(
        filename,
        lambda: post_statbank_csv("PRIS111", variables, timeout=60),
        prefer_cache=prefer_cache,
    )
