from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap
from matplotlib.ticker import PercentFormatter

from ..paths import DATA_FINAL, DATA_PROCESSED, REPORTS_FIGURES, REPORTS_TABLES
from .seaborn_theme import GROUP_COLORS, save_figure, set_theme


FEATURE_GROUPS = {
    "Identifiers": ["year", "group_code", "group_name"],
    "Income": ["income_dkk_per_person", "income_gap_vs_danes", "income_ratio_vs_danes", "base_year_index"],
    "Population": ["population", "population_share", "immigrant_origin_share"],
    "Contribution": ["income_share", "contribution_index"],
    "Births": ["birth_share", "birth_population_ratio"],
    "Migration": ["immigration_count", "emigration_count", "net_migration"],
    "Real income": ["real_income_dkk_per_person"],
}


def _read_csv(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _year_range(df: pd.DataFrame) -> tuple[int | None, int | None]:
    if df.empty or "year" not in df.columns:
        return None, None
    years = pd.to_numeric(df["year"], errors="coerce").dropna()
    if years.empty:
        return None, None
    return int(years.min()), int(years.max())


def _inventory(
    income_features: pd.DataFrame,
    population_features: pd.DataFrame,
    contribution_features: pd.DataFrame,
    demo_features: pd.DataFrame,
) -> pd.DataFrame:
    births = _read_csv(DATA_PROCESSED / "births_long.csv")
    migration = _read_csv(DATA_PROCESSED / "migration_long.csv")
    cpi = _read_csv(DATA_PROCESSED / "cpi_annual.csv")
    rows = [
        ("Income", "INDKP109", income_features, "annual", "DKK per person / thousand DKK", "H2, H3, H4", "Income availability controls latest contribution year."),
        ("Population", "FOLK1E", population_features, "annual Q4 snapshot", "people / share", "H1, H4", "FOLK1E ancestry/origin data start in 2008; no 2000 data are invented."),
        ("Contribution", "INDKP109 + FOLK1E", contribution_features, "annual", "share / index", "H4", "Requires income and population in the same year."),
        ("Births", "FODIE", births, "annual", "live births / share", "H5", "Births are by mother's background, not child ancestry classification."),
        ("Migration", "VAN1AAR + VAN2AAR", migration, "annual", "people", "H5", "Citizenship-based migration proxy."),
        ("CPI / real income", "PRIS111", cpi, "annual average of monthly index", "index / real DKK", "H3", "Used for real-income adjustment."),
        ("Combined ML-ready", "Engineered merge", _read_csv(DATA_FINAL / "ml_ready_denmark_income_demography.csv"), "annual", "mixed", "H2-H5", "Merged analytical dataset; gaps are mostly structural."),
    ]
    out = []
    for block, source, df, freq, unit, used, note in rows:
        first, latest = _year_range(df)
        out.append(
            {
                "dataset_block": block,
                "source_table": source,
                "first_year": first,
                "latest_year": latest,
                "frequency": freq,
                "unit": unit,
                "used_in_hypotheses": used,
                "note": note,
            }
        )
    return pd.DataFrame(out)


def _latest_snapshot(
    income_features: pd.DataFrame,
    population_features: pd.DataFrame,
    contribution_features: pd.DataFrame,
    demo_features: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    if not income_features.empty:
        latest_year = int(income_features["year"].max())
        latest = income_features[income_features["year"] == latest_year]
        for _, row in latest.iterrows():
            rows.append({"metric": "Taxable income per person", "group": row["group_name"], "value": row["income_dkk_per_person"], "unit": "DKK/person", "latest_year": latest_year, "source_table": "INDKP109", "used_in_hypothesis": "H2, H3", "interpretation_note": "Latest complete income year."})
            rows.append({"metric": "Income ratio vs Danish origin", "group": row["group_name"], "value": row["income_ratio_vs_danes"], "unit": "ratio", "latest_year": latest_year, "source_table": "INDKP109", "used_in_hypothesis": "H2", "interpretation_note": "1.0 means same as Danish-origin income."})
    if not population_features.empty:
        latest_year = int(population_features["year"].max())
        latest = population_features[population_features["year"] == latest_year]
        for _, row in latest.iterrows():
            rows.append({"metric": "Population share", "group": row["group_name"], "value": row["population_share"], "unit": "share", "latest_year": latest_year, "source_table": "FOLK1E", "used_in_hypothesis": "H1, H4", "interpretation_note": "Latest available population year."})
    if not contribution_features.empty:
        latest_year = int(contribution_features["year"].max())
        latest = contribution_features[contribution_features["year"] == latest_year]
        for _, row in latest.iterrows():
            rows.append({"metric": "Contribution index", "group": row["group_name"], "value": row["contribution_index"], "unit": "index", "latest_year": latest_year, "source_table": "INDKP109 + FOLK1E", "used_in_hypothesis": "H4", "interpretation_note": "1.0 means proportional taxable-income representation."})
    if not demo_features.empty:
        latest_year = int(demo_features["year"].max())
        latest = demo_features[(demo_features["year"] == latest_year) & demo_features.get("birth_population_ratio", pd.Series(dtype=float)).notna()]
        for _, row in latest.iterrows():
            rows.append({"metric": "Birth-population ratio", "group": row["group_name"], "value": row["birth_population_ratio"], "unit": "ratio", "latest_year": latest_year, "source_table": "FODIE + FOLK1E", "used_in_hypothesis": "H5", "interpretation_note": "Births by mother's background; 1.0 equals population share."})
    return pd.DataFrame(rows)


def _format_value(value, unit):
    if pd.isna(value):
        return ""
    if unit == "share":
        return f"{value:.1%}"
    if unit in {"ratio", "index"}:
        return f"{value:.2f}"
    if abs(value) >= 1000:
        return f"{value / 1000:.0f}k"
    return f"{value:.1f}"


def create_overview_plots(
    income_features: pd.DataFrame,
    population_features: pd.DataFrame,
    contribution_features: pd.DataFrame,
    demo_features: pd.DataFrame,
) -> None:
    set_theme()
    outdir = REPORTS_FIGURES / "overview"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.png"):
        old.unlink()

    inventory = _inventory(income_features, population_features, contribution_features, demo_features)
    snapshot = _latest_snapshot(income_features, population_features, contribution_features, demo_features)
    inventory.to_csv(REPORTS_TABLES / "overview_dataset_inventory.csv", index=False)
    snapshot.to_csv(REPORTS_TABLES / "overview_latest_snapshot.csv", index=False)

    plot_inv = inventory.dropna(subset=["first_year", "latest_year"]).iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    palette = sns.color_palette("deep", n_colors=len(plot_inv))
    for i, row in plot_inv.iterrows():
        ax.barh(i, row["latest_year"] - row["first_year"] + 0.8, left=row["first_year"] - 0.4, color=palette[i], height=0.55)
        ax.text(row["latest_year"] + 0.15, i, f"{int(row['first_year'])}-{int(row['latest_year'])}", va="center", fontsize=9)
    common = int(min(
        inventory.loc[inventory["dataset_block"] == "Income", "latest_year"].iloc[0],
        inventory.loc[inventory["dataset_block"] == "Population", "latest_year"].iloc[0],
    ))
    ax.axvline(common, color="black", linestyle=":", linewidth=1.4)
    ax.text(common + 0.1, len(plot_inv) - 0.2, f"Latest common income-population year: {common}", fontsize=9)
    ax.set_yticks(range(len(plot_inv)))
    ax.set_yticklabels(plot_inv["dataset_block"])
    ax.set_xlabel("Calendar year")
    ax.set_title("Dataset coverage timeline")
    save_figure(fig, outdir / "01_dataset_coverage_timeline.png")

    blocks = {
        "Income": income_features,
        "Population": population_features,
        "Contribution": contribution_features,
        "Births / migration": demo_features,
        "ML-ready": _read_csv(DATA_FINAL / "ml_ready_denmark_income_demography.csv"),
    }
    values = []
    labels = []
    status_map = {"missing": 0, "not applicable": 1, "partial": 2, "available": 3}
    for _, df in blocks.items():
        value_row = []
        label_row = []
        for features in FEATURE_GROUPS.values():
            available = [col for col in features if col in df.columns]
            if df.empty:
                label = "missing"
            elif not available:
                label = "not applicable"
            elif len(available) < len(features):
                label = "partial"
            else:
                label = "available"
            value_row.append(status_map[label])
            label_row.append(label)
        values.append(value_row)
        labels.append(label_row)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    sns.heatmap(pd.DataFrame(values, index=blocks.keys(), columns=FEATURE_GROUPS.keys()), annot=pd.DataFrame(labels, index=blocks.keys(), columns=FEATURE_GROUPS.keys()), fmt="", cmap=ListedColormap(["#BDBDBD", "#F2F2F2", "#F2C879", "#4C8D5A"]), cbar=False, linewidths=0.8, linecolor="white", annot_kws={"fontsize": 8}, ax=ax)
    ax.set_title("Feature availability by dataset block")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=25)
    save_figure(fig, outdir / "02_feature_availability_matrix.png")

    if not snapshot.empty:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        panels = [
            ("Taxable income per person", "DKK/person"),
            ("Population share", "share"),
            ("Contribution index", "index"),
        ]
        for ax, (metric, unit) in zip(axes, panels):
            data = snapshot[snapshot["metric"] == metric]
            if data.empty:
                ax.axis("off")
                continue
            sns.barplot(data=data, x="group", y="value", hue="group", palette={g: GROUP_COLORS.get(g, "#6E5794") for g in data["group"]}, legend=False, ax=ax)
            for container in ax.containers:
                ax.bar_label(container, labels=[_format_value(bar.get_height(), unit) for bar in container], fontsize=8)
            if unit == "share":
                ax.yaxis.set_major_formatter(PercentFormatter(1))
            if unit == "index":
                ax.axhline(1, color="black", linestyle=":", linewidth=1)
            ax.set_title(f"{metric}\nYear: {int(data['latest_year'].max())}")
            ax.set_xlabel("")
            ax.set_ylabel(unit)
            ax.tick_params(axis="x", rotation=20)
        fig.suptitle("Latest project snapshot dashboard", fontsize=16, fontweight="bold")
        save_figure(fig, outdir / "03_latest_project_snapshot_dashboard.png")
