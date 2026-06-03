from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..paths import REPORTS_FIGURES
from .seaborn_theme import GROUP_COLORS, save_figure, set_theme


def _clean(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for path in outdir.glob("*.png"):
        path.unlink()


def _bar_labels(ax, fmt="{:.2f}"):
    for container in ax.containers:
        ax.bar_label(container, labels=[fmt.format(bar.get_height()) for bar in container], fontsize=8, padding=2)


def create_hypothesis_04_plots(contribution_features: pd.DataFrame) -> None:
    set_theme()
    outdir = REPORTS_FIGURES / "hypothesis_04_contribution_index"
    _clean(outdir)
    if contribution_features.empty:
        return
    palette = {name: GROUP_COLORS.get(name, "#6E5794") for name in contribution_features["group_name"].unique()}

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.lineplot(data=contribution_features, x="year", y="contribution_index", hue="group_name", palette=palette, marker="o", ax=ax)
    ax.axhline(1, color="black", linestyle=":", linewidth=1)
    ax.set_title("Contribution index over time")
    ax.set_ylabel("Income share / population share")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    save_figure(fig, outdir / "01_contribution_index_over_time.png")

    latest = contribution_features[contribution_features["year"] == contribution_features["year"].max()].copy()
    latest["gap_from_1"] = latest["contribution_index"] - 1
    latest["income_share_minus_population_share"] = latest["income_share"] - latest["population_share"]

    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=latest, x="group_name", y="contribution_index", hue="group_name", palette=palette, legend=False, ax=ax)
    ax.axhline(1, color="black", linestyle=":", linewidth=1)
    ax.tick_params(axis="x", rotation=18)
    ax.set_title(f"Latest contribution index ({int(latest['year'].max())})")
    ax.set_xlabel("")
    ax.set_ylabel("Index")
    _bar_labels(ax)
    save_figure(fig, outdir / "02_latest_contribution_index.png")

    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=latest, x="group_name", y="gap_from_1", hue="group_name", palette=palette, legend=False, ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.tick_params(axis="x", rotation=18)
    ax.set_title("Latest gap from proportionality")
    ax.set_xlabel("")
    ax.set_ylabel("Contribution index - 1.0")
    _bar_labels(ax)
    save_figure(fig, outdir / "03_latest_gap_from_proportionality.png")

    fig, ax = plt.subplots(figsize=(11, 6))
    data = contribution_features.copy()
    data["income_share_minus_population_share"] = data["income_share"] - data["population_share"]
    sns.lineplot(data=data, x="year", y="income_share_minus_population_share", hue="group_name", palette=palette, marker="o", ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Income share minus population share")
    ax.set_ylabel("Share-point gap")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    save_figure(fig, outdir / "04_income_share_minus_population_share.png")

    heat = contribution_features.pivot(index="group_name", columns="year", values="contribution_index")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    sns.heatmap(heat, cmap="vlag", center=1, annot=True, fmt=".2f", ax=ax)
    ax.set_title("Contribution index heatmap")
    ax.set_ylabel("")
    save_figure(fig, outdir / "05_contribution_index_heatmap.png")
