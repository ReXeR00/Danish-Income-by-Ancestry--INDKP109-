from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from ..paths import DATA_RAW


def cache_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def save_raw_csv(csv_text: str, filename: str, directory: Path = DATA_RAW) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(csv_text, encoding="utf-8")
    return path


def load_cached_csv(filename: str, directory: Path = DATA_RAW) -> pd.DataFrame:
    path = directory / filename
    if not cache_exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, sep=";")


def load_or_fetch(
    filename: str,
    fetcher: Callable[[], str],
    *,
    directory: Path = DATA_RAW,
    prefer_cache: bool = True,
) -> pd.DataFrame:
    path = directory / filename
    if prefer_cache and cache_exists(path):
        return pd.read_csv(path, sep=";")
    csv_text = fetcher()
    save_raw_csv(csv_text, filename, directory)
    return pd.read_csv(path, sep=";")
