from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

STATBANK_API_URL = "https://api.statbank.dk/v1/data"
STATBANK_TABLEINFO_URL = "https://api.statbank.dk/v1/tableinfo/{table}"


class StatBankError(RuntimeError):
    """Readable exception for StatBank API failures."""


def build_payload(
    table: str,
    variables: dict[str, list[str]],
    *,
    file_format: str = "CSV",
    value_presentation: str = "Code",
) -> dict[str, Any]:
    return {
        "table": table,
        "format": file_format,
        "valuePresentation": value_presentation,
        "variables": [{"code": code, "values": values} for code, values in variables.items()],
    }


def post_statbank_csv(
    table: str,
    variables: dict[str, list[str]],
    *,
    file_format: str = "CSV",
    timeout: int = 60,
) -> str:
    payload = build_payload(table, variables, file_format=file_format)
    try:
        response = requests.post(STATBANK_API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise StatBankError(f"StatBank request timed out for table {table}.") from exc
    except requests.HTTPError as exc:
        message = response.text[:500] if "response" in locals() else str(exc)
        raise StatBankError(f"StatBank HTTP error for table {table}: {message}") from exc
    except requests.RequestException as exc:
        raise StatBankError(f"StatBank request failed for table {table}: {exc}") from exc
    return response.text


def parse_statbank_csv(csv_text: str) -> pd.DataFrame:
    if not csv_text.strip():
        return pd.DataFrame()
    return pd.read_csv(StringIO(csv_text), sep=";")


def fetch_statbank_dataframe(
    table: str,
    variables: dict[str, list[str]],
    *,
    file_format: str = "CSV",
    timeout: int = 60,
) -> pd.DataFrame:
    return parse_statbank_csv(post_statbank_csv(table, variables, file_format=file_format, timeout=timeout))


def get_table_info(table: str, *, lang: str = "en", timeout: int = 30) -> dict[str, Any]:
    try:
        response = requests.get(
            STATBANK_TABLEINFO_URL.format(table=table),
            params={"lang": lang, "format": "JSON"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise StatBankError(f"Could not read StatBank metadata for {table}: {exc}") from exc
    return response.json()


def variable_values(table: str, variable_id: str) -> list[str]:
    info = get_table_info(table)
    for variable in info.get("variables", []):
        if variable.get("id") == variable_id:
            return [value["id"] for value in variable.get("values", [])]
    raise StatBankError(f"Variable {variable_id} was not found in table {table}.")


def available_years(table: str) -> list[int]:
    info = get_table_info(table)
    for variable in info.get("variables", []):
        if variable.get("id") == "Tid":
            years: list[int] = []
            for value in variable.get("values", []):
                raw = str(value["id"])
                if raw.isdigit():
                    years.append(int(raw))
                elif raw[:4].isdigit() and ("K" in raw or "M" in raw):
                    years.append(int(raw[:4]))
            return sorted(set(years))
    return []
