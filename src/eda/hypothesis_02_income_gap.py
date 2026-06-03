from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression

from ..paths import REPORTS_FIGURES
from .seaborn_theme import GROUP_COLORS, save_figure, set_theme


def _clean(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for path in outdir.glob("*.png"):
        path.unlink()


def _bar_labels(ax, fmt):
    for container in ax.containers:
        ax.bar_label(container, labels=[fmt(bar.get_height()) for bar in container], fontsize=8, padding=2)


def _line_latest(ax, df, y_col):
    latest_year = df["year"].max()
    for _, row in df[df["year"] == latest_year].iterrows():
        ax.annotate(f"{row['group_name']}: {row[y_col]:.2f}" if "ratio" in y_col else f"{row['group_name']}: {row[y_col]/1000:.0f}k", (row["year"], row[y_col]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9)


def _gap_forecast(gap: pd.DataFrame, horizon: int = 10) -> pd.DataFrame:
    rows = []
    for group_code, group in gap.groupby("group_code"):
        clean = group.dropna(subset=["income_gap_vs_danes"])
        if len(clean) < 2:
            continue
        model = LinearRegression().fit(clean[["year"]], clean["income_gap_vs_danes"])
        for year in range(int(clean["year"].max()) + 1, int(clean["year"].max()) + horizon + 1):
            rows.append(
                {
                    "year": year,
                    "group_code": group_code,
                    "group_name": clean["group_name"].iloc[0],
                    "forecast_income_gap_vs_danes": float(model.predict(pd.DataFrame({"year": [year]}))[0]),
                }
            )
    return pd.DataFrame(rows)


def create_hypothesis_02_plots(income_features: pd.DataFrame) -> None:
    set_theme()
    outdir = REPORTS_FIGURES / "hypothesis_02_income_gap"
    _clean(outdir)
    if income_features.empty:
        return
    palette = {name: GROUP_COLORS.get(name, "#6E5794") for name in income_features["group_name"].unique()}

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=income_features, x="year", y="income_dkk_per_person", hue="group_name", palette=palette, marker="o", ax=ax)
    ax.set_title("Taxable income per person over time")
    ax.set_ylabel("DKK per person")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _line_latest(ax, income_features, "income_dkk_per_person")
    save_figure(fig, outdir / "01_income_per_person_over_time.png")

    gap = income_features[income_features["group_code"] != "DANSK"].copy()
    gap_palette = {name: GROUP_COLORS.get(name, "#6E5794") for name in gap["group_name"].unique()}
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=gap, x="year", y="income_ratio_vs_danes", hue="group_name", palette=gap_palette, marker="o", ax=ax)
    ax.axhline(1, color="black", linestyle=":", linewidth=1)
    ax.set_title("Income ratio vs Danish origin")
    ax.set_ylabel("Ratio")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _line_latest(ax, gap, "income_ratio_vs_danes")
    save_figure(fig, outdir / "02_income_ratio_vs_danish_origin.png")

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=gap, x="year", y="income_gap_vs_danes", hue="group_name", palette=gap_palette, marker="o", ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Income gap vs Danish origin")
    ax.set_ylabel("DKK per person gap")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _line_latest(ax, gap, "income_gap_vs_danes")
    save_figure(fig, outdir / "03_income_gap_vs_danish_origin.png")

    latest = income_features[income_features["year"] == income_features["year"].max()]
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=latest, x="group_name", y="income_dkk_per_person", hue="group_name", palette=palette, legend=False, ax=ax)
    ax.tick_params(axis="x", rotation=18)
    ax.set_title(f"Latest-year income comparison ({int(latest['year'].max())})")
    ax.set_xlabel("")
    ax.set_ylabel("DKK per person")
    _bar_labels(ax, lambda value: f"{value/1000:.0f}k")
    save_figure(fig, outdir / "04_latest_year_income_comparison.png")

    forecast = _gap_forecast(gap)
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=gap, x="year", y="income_gap_vs_danes", hue="group_name", palette=gap_palette, marker="o", ax=ax)
    if not forecast.empty:
        sns.lineplot(data=forecast, x="year", y="forecast_income_gap_vs_danes", hue="group_name", palette=gap_palette, linestyle="--", legend=False, ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Gap-closing scenario: next 10 years")
    ax.set_ylabel("DKK per person gap")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    save_figure(fig, outdir / "05_gap_closing_forecast_next_10_years.png")
