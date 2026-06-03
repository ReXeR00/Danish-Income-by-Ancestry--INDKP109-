from __future__ import annotations

import pandas as pd

GROUP_NAMES = {
    "DANSK": "Danish origin",
    "IND_VEST": "Western immigrant origin",
    "IND_ANDRE": "Non-western immigrant origin",
    "UNKNOWN": "Unknown origin",
}

POPULATION_GROUP_MAP = {
    "1": "DANSK",
    "24": "IND_VEST",
    "34": "IND_VEST",
    "25": "IND_ANDRE",
    "35": "IND_ANDRE",
}

BIRTH_GROUP_MAP = {
    "5": "DANSK",
    "4": "IMMIGRANT_MOTHER",
    "3": "DESCENDANT_MOTHER",
    "0": "UNKNOWN",
}

MIGRATION_GROUP_NAMES = {
    "DANISH_CITIZENSHIP": "Danish citizenship",
    "FOREIGN_CITIZENSHIP": "Foreign citizenship",
}


def _find_col(df: pd.DataFrame, expected: str) -> str:
    if expected in df.columns:
        return expected
    lowered = {str(col).lower(): col for col in df.columns}
    if expected.lower() in lowered:
        return lowered[expected.lower()]
    raise KeyError(f"Expected column {expected!r}; found {list(df.columns)}")


def _clean_value_column(df: pd.DataFrame) -> pd.Series:
    value_col = _find_col(df, "INDHOLD")
    values = df[value_col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(values, errors="coerce")


def clean_income_long(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    df["year"] = pd.to_numeric(df[_find_col(df, "TID")], errors="coerce").astype("Int64")
    df["group_code"] = df[_find_col(df, "HERKOMST")].astype(str)
    df["group_name"] = df["group_code"].map(GROUP_NAMES).fillna(df["group_code"])
    df["unit_code"] = df[_find_col(df, "ENHED")].astype(str)
    df["value"] = _clean_value_column(df)
    per_person = (
        df[df["unit_code"] == "121"][["year", "group_code", "group_name", "value"]]
        .rename(columns={"value": "income_dkk_per_person"})
    )
    totals = (
        df[df["unit_code"] == "110"][["year", "group_code", "value"]]
        .rename(columns={"value": "total_income_thousand_dkk"})
    )
    out = per_person.merge(totals, on=["year", "group_code"], how="outer")
    out["group_name"] = out["group_code"].map(GROUP_NAMES).fillna(out["group_code"])
    return out.sort_values(["year", "group_code"]).reset_index(drop=True)


def clean_population_long(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    tid = _find_col(df, "TID")
    df["year"] = df[tid].astype(str).str[:4].astype(int)
    df["group_code"] = df[_find_col(df, "HERKOMST")].astype(str).map(POPULATION_GROUP_MAP)
    df["population"] = _clean_value_column(df)
    df = df.dropna(subset=["group_code", "population"])
    out = df.groupby(["year", "group_code"], as_index=False)["population"].sum()
    out["group_name"] = out["group_code"].map(GROUP_NAMES)
    return out[["year", "group_code", "group_name", "population"]].sort_values(["year", "group_code"])


def clean_births_long(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    df["year"] = pd.to_numeric(df[_find_col(df, "TID")], errors="coerce").astype("Int64")
    df["mother_group_code"] = df[_find_col(df, "MOHERK")].astype(str).map(BIRTH_GROUP_MAP)
    df["births"] = _clean_value_column(df)
    df = df.dropna(subset=["mother_group_code", "births"])
    out = df.groupby(["year", "mother_group_code"], as_index=False)["births"].sum()
    name_map = {
        "DANSK": "Mother of Danish origin",
        "IMMIGRANT_MOTHER": "Immigrant mother",
        "DESCENDANT_MOTHER": "Descendant mother",
        "UNKNOWN": "Unknown mother origin",
    }
    out["mother_group_name"] = out["mother_group_code"].map(name_map)
    return out[["year", "mother_group_code", "mother_group_name", "births"]].sort_values(["year", "mother_group_code"])


def clean_migration_long(immigration_raw: pd.DataFrame, emigration_raw: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for raw, flow in [(immigration_raw, "immigration"), (emigration_raw, "emigration")]:
        if raw.empty:
            continue
        df = raw.copy()
        df["year"] = pd.to_numeric(df[_find_col(df, "TID")], errors="coerce").astype("Int64")
        df["migration_group_code"] = df[_find_col(df, "STATSB")].astype(str).apply(
            lambda x: "DANISH_CITIZENSHIP" if x == "5100" else "FOREIGN_CITIZENSHIP"
        )
        df[flow] = _clean_value_column(df)
        frames.append(df.groupby(["year", "migration_group_code"], as_index=False)[flow].sum())
    if not frames:
        return pd.DataFrame()
    out = frames[0]
    for frame in frames[1:]:
        out = out.merge(frame, on=["year", "migration_group_code"], how="outer")
    out["immigration"] = out.get("immigration", 0).fillna(0)
    out["emigration"] = out.get("emigration", 0).fillna(0)
    out["net_migration"] = out["immigration"] - out["emigration"]
    out["migration_group_name"] = out["migration_group_code"].map(MIGRATION_GROUP_NAMES)
    return out.sort_values(["year", "migration_group_code"]).reset_index(drop=True)


def clean_cpi_annual(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    df["year"] = df[_find_col(df, "TID")].astype(str).str[:4].astype(int)
    df["cpi_index"] = _clean_value_column(df)
    out = df.groupby("year", as_index=False)["cpi_index"].mean()
    latest_index = out.loc[out["year"].idxmax(), "cpi_index"]
    out["cpi_deflator_to_latest"] = latest_index / out["cpi_index"]
    return out.sort_values("year")
