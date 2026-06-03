from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_FINAL = ROOT / "data" / "final"
REPORTS = ROOT / "reports"
REPORTS_FIGURES = REPORTS / "figures"
REPORTS_TABLES = REPORTS / "tables"


def ensure_project_dirs() -> None:
    for path in [
        DATA_RAW,
        DATA_PROCESSED,
        DATA_FINAL,
        REPORTS_TABLES,
        REPORTS_FIGURES / "overview",
        REPORTS_FIGURES / "hypothesis_01_population_share",
        REPORTS_FIGURES / "hypothesis_02_income_gap",
        REPORTS_FIGURES / "hypothesis_03_relative_income_growth",
        REPORTS_FIGURES / "hypothesis_04_contribution_index",
        REPORTS_FIGURES / "hypothesis_05_births_migration",
    ]:
        path.mkdir(parents=True, exist_ok=True)
