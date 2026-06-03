from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..paths import REPORTS_FIGURES, REPORTS_TABLES
from .seaborn_theme import GROUP_COLORS, save_figure, set_theme


def _clean(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for path in outdir.glob("*.png"):
        path.unlink()


def _labels(ax, fmt="{:.1f}%"):
    for container in ax.containers:
        ax.bar_label(container, labels=[fmt.format(bar.get_height()) for bar in container], fontsize=8, padding=2)


def create_hypothesis_03_plots(income_features: pd.DataFrame) -> None:
    set_theme()
    outdir = REPORTS_FIGURES / "hypothesis_03_relative_income_growth"
    _clean(outdir)
    if income_features.empty:
        return
    palette = {name: GROUP_COLORS.get(name, "#6E5794") for name in income_features["group_name"].unique()}

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=income_features, x="year", y="base_year_index", hue="group_name", palette=palette, marker="o", ax=ax)
    ax.axhline(100, color="black", linestyle=":", linewidth=1)
    ax.set_title("Base-year income index")
    ax.set_ylabel("Index, first observed year = 100")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    save_figure(fig, outdir / "01_base_year_income_index.png")

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=income_features, x="year", y="yoy_change_pct", hue="group_name", palette=palette, marker="o", ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Year-over-year taxable-income change")
    ax.set_ylabel("YoY change (%)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    save_figure(fig, outdir / "02_yoy_percentage_change.png")

    ranked = income_features.dropna(subset=["yoy_change_pct"]).sort_values("yoy_change_pct", ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(11, 6))
    ranked = ranked.assign(label=ranked["group_name"] + " (" + ranked["year"].astype(str) + ")")
    sns.barplot(data=ranked, y="label", x="yoy_change_pct", hue="group_name", palette=palette, dodge=False, ax=ax)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Ranked strongest YoY taxable-income changes")
    ax.set_xlabel("YoY change (%)")
    ax.set_ylabel("")
    ax.legend(loc="lower right", title="")
    save_figure(fig, outdir / "03_ranked_yoy_income_changes.png")

    growth = income_features.sort_values("year").groupby(["group_code", "group_name"], as_index=False).agg(
        first=("income_dkk_per_person", "first"),
        latest=("income_dkk_per_person", "last"),
    )
    growth["cumulative_growth_pct"] = (growth["latest"] / growth["first"] - 1) * 100
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=growth, x="group_name", y="cumulative_growth_pct", hue="group_name", palette=palette, legend=False, ax=ax)
    ax.tick_params(axis="x", rotation=18)
    ax.set_title("Cumulative nominal taxable-income growth")
    ax.set_xlabel("")
    ax.set_ylabel("Growth (%)")
    _labels(ax)
    save_figure(fig, outdir / "04_cumulative_growth_barplot.png")

    if "real_income_dkk_per_person" in income_features.columns and income_features["real_income_dkk_per_person"].notna().any():
        rows = []
        for _, group in income_features.sort_values("year").groupby(["group_code", "group_name"]):
            rows.append({"group_name": group["group_name"].iloc[0], "growth_type": "Nominal", "growth_pct": (group["income_dkk_per_person"].iloc[-1] / group["income_dkk_per_person"].iloc[0] - 1) * 100})
            rows.append({"group_name": group["group_name"].iloc[0], "growth_type": "Real CPI-adjusted", "growth_pct": (group["real_income_dkk_per_person"].iloc[-1] / group["real_income_dkk_per_person"].iloc[0] - 1) * 100})
        real = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=real, x="group_name", y="growth_pct", hue="growth_type", ax=ax)
        ax.tick_params(axis="x", rotation=18)
        ax.set_title("Nominal vs real cumulative growth")
        ax.set_xlabel("")
        ax.set_ylabel("Growth (%)")
        _labels(ax)
        save_figure(fig, outdir / "05_nominal_vs_real_cumulative_growth.png")
    else:
        (REPORTS_TABLES / "hypothesis_03_real_income_adjustment.csv").write_text(
            "note\nCPI data were unavailable, so the nominal vs real cumulative growth figure was skipped.\n",
            encoding="utf-8",
        )
