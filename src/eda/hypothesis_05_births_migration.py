from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..paths import REPORTS_FIGURES
from .seaborn_theme import PALETTE, save_figure, set_theme


def _clean(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for path in outdir.glob("*.png"):
        path.unlink()


def _birth_shares(births_long: pd.DataFrame) -> pd.DataFrame:
    if births_long.empty:
        return pd.DataFrame()
    births = births_long.copy()
    totals = births.groupby("year", as_index=False)["births"].sum().rename(columns={"births": "total_births"})
    births = births.merge(totals, on="year", how="left")
    births["birth_share"] = births["births"] / births["total_births"]
    return births


def create_hypothesis_05_plots(
    births_long: pd.DataFrame,
    migration_long: pd.DataFrame,
    demo_features: pd.DataFrame,
) -> None:
    set_theme()
    outdir = REPORTS_FIGURES / "hypothesis_05_births_migration"
    _clean(outdir)

    births = _birth_shares(births_long)
    if not births.empty:
        fig, ax = plt.subplots(figsize=(11, 6))
        palette = {name: PALETTE.get(name, "#6E5794") for name in births["mother_group_name"].unique()}
        sns.lineplot(data=births, x="year", y="birth_share", hue="mother_group_name", palette=palette, marker="o", ax=ax)
        ax.set_title("Birth share by mother's background")
        ax.set_ylabel("Share of live births")
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
        save_figure(fig, outdir / "01_birth_share_by_mothers_background.png")

    if not demo_features.empty and "birth_population_ratio" in demo_features.columns:
        demo_births = demo_features.dropna(subset=["birth_population_ratio"]).copy()
        if not demo_births.empty:
            palette = {name: PALETTE.get(name, "#6E5794") for name in demo_births["group_name"].unique()}
            fig, ax = plt.subplots(figsize=(11, 6))
            sns.lineplot(data=demo_births, x="year", y="birth_population_ratio", hue="group_name", palette=palette, marker="o", ax=ax)
            ax.axhline(1, color="black", linestyle=":", linewidth=1)
            ax.set_title("Birth-population ratio")
            ax.set_ylabel("Birth share / population share")
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
            save_figure(fig, outdir / "02_birth_population_ratio.png")

            demo_births["birth_population_gap"] = demo_births["birth_share"] - demo_births["population_share"]
            fig, ax = plt.subplots(figsize=(11, 6))
            sns.lineplot(data=demo_births, x="year", y="birth_population_gap", hue="group_name", palette=palette, marker="o", ax=ax)
            ax.axhline(0, color="black", linewidth=1)
            ax.set_title("Birth share minus population share")
            ax.set_ylabel("Share-point gap")
            ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
            save_figure(fig, outdir / "03_birth_population_gap.png")

    if not migration_long.empty:
        fig, ax = plt.subplots(figsize=(11, 6))
        palette = {name: PALETTE.get(name, "#6E5794") for name in migration_long["migration_group_name"].unique()}
        sns.lineplot(data=migration_long, x="year", y="net_migration", hue="migration_group_name", palette=palette, marker="o", ax=ax)
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title("Net migration by citizenship")
        ax.set_ylabel("Immigration - emigration")
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
        save_figure(fig, outdir / "04_net_migration_by_citizenship.png")

    rows = []
    if not demo_features.empty:
        latest = demo_features[demo_features["year"] == demo_features["year"].max()]
        for _, row in latest.dropna(subset=["birth_population_ratio"]).iterrows():
            rows.append({"metric": "Birth-population ratio", "group": row["group_name"], "value": row["birth_population_ratio"]})
    if not migration_long.empty:
        latest = migration_long[migration_long["year"] == migration_long["year"].max()]
        for _, row in latest.iterrows():
            rows.append({"metric": "Net migration", "group": row["migration_group_name"], "value": row["net_migration"]})
    if rows:
        snap = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(10, 5))
        snap["label"] = snap["metric"] + "\n" + snap["group"]
        sns.barplot(data=snap, x="label", y="value", color="#6E5794", ax=ax)
        ax.axhline(0, color="black", linewidth=1)
        ax.tick_params(axis="x", rotation=15)
        ax.set_title("Latest demographic driver snapshot")
        ax.set_xlabel("")
        ax.set_ylabel("Ratio or people")
        for container in ax.containers:
            ax.bar_label(container, fontsize=8, padding=2)
        save_figure(fig, outdir / "05_latest_demographic_driver_snapshot.png")
