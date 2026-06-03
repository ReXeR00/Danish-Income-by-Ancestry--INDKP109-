from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, PercentFormatter

from ..cleaning.clean_statbank import clean_births_long, clean_population_long
from ..data.load_births import load_births_raw
from ..data.load_population import load_population_raw
from ..features.build_population_features import build_population_features
from ..paths import REPORTS_FIGURES, REPORTS_TABLES
from ..stats.trend_models import (
    fit_linear_trend,
    fit_log_trend,
    fit_logistic_trend,
    predict_linear,
    predict_log,
    predict_logistic,
)
from .seaborn_theme import GROUP_COLORS, PALETTE, save_figure, set_theme

OUTDIR = REPORTS_FIGURES / "hypothesis_01_population_share"
FOOTNOTE_DEATHS = (
    "* Deaths by the same ancestry/origin grouping were not included because a compatible public StatBank "
    "table was not available in the current pipeline. Therefore, this chart compares population shares and "
    "births by mother's background, not a full births-minus-deaths natural change model."
)


def _millions(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value / 1_000_000:.2f}M"


def _pct(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.1%}"


def _pp(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value * 100:+.1f} pp"


def _format_millions_axis(ax) -> None:
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1_000_000:.1f}M"))


def _clean_h1_output_dir() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for path in OUTDIR.glob("*.png"):
        path.unlink()


def _extended_population_features(population_features: pd.DataFrame | None) -> pd.DataFrame:
    if population_features is not None and not population_features.empty and population_features["year"].min() <= 2010:
        return population_features.copy()
    try:
        raw = load_population_raw(start_year=2000, prefer_cache=True)
        cleaned = clean_population_long(raw)
        features = build_population_features(cleaned)
        if not features.empty:
            return features
    except Exception as exc:
        print(f"WARNING: Extended Hypothesis 1 population load failed; using pipeline data. {exc}")
    return population_features.copy() if population_features is not None else pd.DataFrame()


def _extended_births(births_long: pd.DataFrame | None) -> pd.DataFrame:
    if births_long is not None and not births_long.empty and births_long["year"].min() <= 2010:
        return births_long.copy()
    try:
        raw = load_births_raw(start_year=2000, prefer_cache=True)
        cleaned = clean_births_long(raw)
        if not cleaned.empty:
            return cleaned
    except Exception as exc:
        print(f"WARNING: Extended Hypothesis 1 births load failed; using pipeline data. {exc}")
    return births_long.copy() if births_long is not None else pd.DataFrame()


def _population_with_immigrant_total(population_features: pd.DataFrame) -> pd.DataFrame:
    base = population_features.copy()
    immigrant = (
        base[base["group_code"].isin(["IND_VEST", "IND_ANDRE"])]
        .groupby("year", as_index=False)
        .agg(
            population=("population", "sum"),
            total_population=("total_population", "first"),
            immigrant_origin_population=("immigrant_origin_population", "first"),
            immigrant_origin_share=("immigrant_origin_share", "first"),
        )
    )
    immigrant["group_code"] = "IMMIGRANT_TOTAL"
    immigrant["group_name"] = "Immigrant-origin total"
    immigrant["population_share"] = immigrant["population"] / immigrant["total_population"]
    return pd.concat([base, immigrant], ignore_index=True, sort=False)


def _nearest_year(years: list[int], target: int) -> int:
    return min(years, key=lambda year: (abs(year - target), year))


def _milestone_years(population_features: pd.DataFrame) -> pd.DataFrame:
    years = sorted(int(year) for year in population_features["year"].dropna().unique())
    latest = max(years)
    requests = [2000, 2010, 2020, latest]
    rows = []
    seen_actual: set[int] = set()
    for requested in requests:
        actual = latest if requested == latest else _nearest_year(years, requested)
        label = "latest" if requested == latest else str(requested)
        if requested != actual and requested == 2000:
            label = f"2000 target / nearest available: {actual}"
        if actual in seen_actual and label != "latest":
            continue
        seen_actual.add(actual)
        rows.append(
            {
                "milestone_label": label,
                "requested_milestone_year": requested,
                "actual_year_used": actual,
                "note": "exact year" if requested == actual else f"nearest available year to {requested}",
            }
        )
    return pd.DataFrame(rows)


def _build_population_milestone_table(population_all: pd.DataFrame, milestones: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, milestone in milestones.iterrows():
        year = int(milestone["actual_year_used"])
        year_df = population_all[population_all["year"] == year]
        for _, row in year_df.iterrows():
            if row["group_name"] not in GROUP_COLORS:
                continue
            rows.append(
                {
                    **milestone.to_dict(),
                    "year": year,
                    "group_code": row["group_code"],
                    "group_name": row["group_name"],
                    "population": row["population"],
                    "total_population": row["total_population"],
                    "population_share": row["population_share"],
                    "immigrant_origin_population": row["immigrant_origin_population"],
                    "immigrant_origin_share": row["immigrant_origin_share"],
                }
            )
    return pd.DataFrame(rows)


def _build_population_changes(population_all: pd.DataFrame, milestones: pd.DataFrame) -> pd.DataFrame:
    actual_by_request = {
        int(row["requested_milestone_year"]): int(row["actual_year_used"])
        for _, row in milestones.iterrows()
        if row["milestone_label"] != "latest"
    }
    latest_year = int(milestones[milestones["milestone_label"] == "latest"]["actual_year_used"].iloc[0])
    periods = [
        ("2000 to 2010", actual_by_request.get(2000), actual_by_request.get(2010)),
        ("2010 to 2020", actual_by_request.get(2010), actual_by_request.get(2020)),
        ("2020 to latest", actual_by_request.get(2020), latest_year),
        ("2000 to latest", actual_by_request.get(2000), latest_year),
    ]
    rows = []
    for period, start_year, end_year in periods:
        if start_year is None or end_year is None:
            continue
        for group_name in GROUP_COLORS:
            start = population_all[(population_all["year"] == start_year) & (population_all["group_name"] == group_name)]
            end = population_all[(population_all["year"] == end_year) & (population_all["group_name"] == group_name)]
            if start.empty or end.empty:
                continue
            start_row = start.iloc[0]
            end_row = end.iloc[0]
            rows.append(
                {
                    "period": period,
                    "start_year_used": start_year,
                    "end_year_used": end_year,
                    "group_name": group_name,
                    "start_population": start_row["population"],
                    "end_population": end_row["population"],
                    "change_abs": end_row["population"] - start_row["population"],
                    "change_pct": (end_row["population"] / start_row["population"] - 1) if start_row["population"] else np.nan,
                    "start_population_share": start_row["population_share"],
                    "end_population_share": end_row["population_share"],
                    "change_percentage_points": end_row["population_share"] - start_row["population_share"],
                }
            )
    changes = pd.DataFrame(rows)
    if changes.empty:
        return changes
    latest_year = int(milestones[milestones["milestone_label"] == "latest"]["actual_year_used"].iloc[0])
    baseline_years = {
        "2000": actual_by_request.get(2000),
        "2010": actual_by_request.get(2010),
        "2020": actual_by_request.get(2020),
    }
    for group_name in changes["group_name"].unique():
        latest = population_all[(population_all["year"] == latest_year) & (population_all["group_name"] == group_name)]
        if latest.empty:
            continue
        latest_row = latest.iloc[0]
        mask = changes["group_name"] == group_name
        for label, baseline_year in baseline_years.items():
            baseline = population_all[
                (population_all["year"] == baseline_year) & (population_all["group_name"] == group_name)
            ]
            if baseline.empty:
                continue
            baseline_row = baseline.iloc[0]
            changes.loc[mask, f"change_since_{label}_abs"] = latest_row["population"] - baseline_row["population"]
            changes.loc[mask, f"change_since_{label}_percentage_points"] = (
                latest_row["population_share"] - baseline_row["population_share"]
            )
            if label == "2000":
                changes.loc[mask, "change_since_2000_pct"] = (
                    latest_row["population"] / baseline_row["population"] - 1
                    if baseline_row["population"]
                    else np.nan
                )
    return changes


def _build_births_summary(births_long: pd.DataFrame, population_all: pd.DataFrame) -> pd.DataFrame:
    if births_long.empty:
        return pd.DataFrame()
    births = births_long.copy()
    births["mother_background_group"] = births["mother_group_code"].map(
        {
            "DANSK": "Mother of Danish origin",
            "IMMIGRANT_MOTHER": "Mothers with immigrant background",
            "DESCENDANT_MOTHER": "Mothers with immigrant background",
            "UNKNOWN": "Unknown mother background",
        }
    )
    births = births.dropna(subset=["mother_background_group"])
    grouped = births.groupby(["year", "mother_background_group"], as_index=False)["births"].sum()
    totals = grouped.groupby("year", as_index=False)["births"].sum().rename(columns={"births": "total_births"})
    grouped = grouped.merge(totals, on="year", how="left")
    grouped["birth_share"] = grouped["births"] / grouped["total_births"]
    pop_map = population_all[population_all["group_name"].isin(["Danish origin", "Immigrant-origin total"])].copy()
    pop_map["mother_background_group"] = pop_map["group_name"].map(
        {
            "Danish origin": "Mother of Danish origin",
            "Immigrant-origin total": "Mothers with immigrant background",
        }
    )
    grouped = grouped.merge(
        pop_map[["year", "mother_background_group", "population_share"]],
        on=["year", "mother_background_group"],
        how="left",
    )
    grouped = grouped.rename(columns={"population_share": "corresponding_population_share"})
    grouped["birth_population_ratio"] = grouped["birth_share"] / grouped["corresponding_population_share"]
    return grouped.sort_values(["year", "mother_background_group"])


def _build_scenarios(population_features: pd.DataFrame, horizon: int = 120) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    observed = population_features[["year", "immigrant_origin_share", "total_population"]].drop_duplicates().dropna()
    observed = observed.sort_values("year")
    if len(observed) < 2:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    latest_year = int(observed["year"].max())
    years = np.arange(int(observed["year"].min()), latest_year + horizon + 1)
    share = observed[["year", "immigrant_origin_share"]]
    total_model = fit_linear_trend(observed[["year", "total_population"]], "year", "total_population")
    projected_total = predict_linear(total_model, years.astype(float))
    models = {
        "linear": (
            "Linear",
            "Assumes constant annual change.",
            fit_linear_trend(share, "year", "immigrant_origin_share"),
            predict_linear,
        ),
        "logarithmic": (
            "Logarithmic",
            "Assumes growth slows over time.",
            fit_log_trend(share, "year", "immigrant_origin_share"),
            predict_log,
        ),
        "logistic": (
            "Logistic",
            "Assumes growth approaches a ceiling.",
            fit_logistic_trend(share, "year", "immigrant_origin_share"),
            predict_logistic,
        ),
    }
    scenario_frames = []
    metric_rows = []
    crossing_rows = []
    thresholds = [0.20, 0.25, 0.33, 0.50, 0.75, 1.00]
    for model_key, (model_label, explanation, info, predict_fn) in models.items():
        preds = np.clip(predict_fn(info, years.astype(float)), 0, 1.5)
        scenario = pd.DataFrame(
            {
                "year": years,
                "model": model_key,
                "model_label": model_label,
                "immigrant_origin_share": preds,
                "projected_total_population": projected_total,
            }
        )
        scenario["projected_immigrant_origin_population"] = (
            scenario["immigrant_origin_share"] * scenario["projected_total_population"]
        )
        scenario["period"] = np.where(scenario["year"] <= latest_year, "fitted historical period", "scenario period")
        scenario_frames.append(scenario)
        metrics = info.get("metrics", {})
        metric_rows.append(
            {
                "model": model_key,
                "model_label": model_label,
                "model_assumption": explanation,
                "r_squared": metrics.get("r2"),
                "rmse": metrics.get("rmse"),
                "mae": metrics.get("mae"),
                "latest_observed_year": latest_year,
                "latest_observed_share": observed["immigrant_origin_share"].iloc[-1],
                "note": info.get("warning", "Scenario model, not an official forecast."),
            }
        )
        for threshold in thresholds:
            note = "Crossing years depend strongly on model assumptions."
            if threshold >= 1:
                note = "100% is a mathematical boundary case, not a realistic forecast threshold."
            future = scenario[scenario["year"] > latest_year]
            reached = future[future["immigrant_origin_share"] >= threshold]
            if reached.empty or (threshold >= 1 and model_key in {"logarithmic", "logistic"}):
                crossing_rows.append(
                    {
                        "model": model_key,
                        "threshold": threshold,
                        "crossing_year": "not reached" if threshold < 1 else "not meaningful",
                        "projected_immigrant_origin_share": np.nan,
                        "projected_total_population": np.nan,
                        "projected_immigrant_origin_population": np.nan,
                        "note": note,
                    }
                )
            else:
                row = reached.iloc[0]
                crossing_rows.append(
                    {
                        "model": model_key,
                        "threshold": threshold,
                        "crossing_year": int(row["year"]),
                        "projected_immigrant_origin_share": row["immigrant_origin_share"],
                        "projected_total_population": row["projected_total_population"],
                        "projected_immigrant_origin_population": row["projected_immigrant_origin_population"],
                        "note": note,
                    }
                )
    return pd.concat(scenario_frames, ignore_index=True), pd.DataFrame(metric_rows), pd.DataFrame(crossing_rows)


def _write_notes(population_features: pd.DataFrame, births_summary: pd.DataFrame, milestones: pd.DataFrame) -> None:
    pop_start = int(population_features["year"].min()) if not population_features.empty else "unavailable"
    pop_end = int(population_features["year"].max()) if not population_features.empty else "unavailable"
    milestone_lines = "\n".join(
        f"- Requested {row['requested_milestone_year']}: used {row['actual_year_used']} ({row['note']})."
        for _, row in milestones.iterrows()
    )
    text = f"""# Hypothesis 1 Notes and Limitations

## Data coverage

- Population table used in the current pipeline: `FOLK1E`.
- Population coverage used for Hypothesis 1: {pop_start} to {pop_end}.

## Milestone-year handling

{milestone_lines}

## Model assumptions

The linear, logarithmic, and logistic curves are scenario models. They are illustrative extrapolations, not official forecasts. Crossing years depend strongly on the model assumption, horizon, and the period used for fitting.

## Scope limitation

Hypothesis 1 is limited to population composition and share scenarios. Births and migration context are handled in Hypothesis 5.
"""
    (REPORTS_TABLES / "hypothesis_01_notes_and_limitations.md").write_text(text, encoding="utf-8")


def _direct_line_labels(ax, df: pd.DataFrame, y_col: str, label_template, offset: int = 8) -> None:
    latest_year = df["year"].max()
    for _, row in df[df["year"] == latest_year].iterrows():
        ax.annotate(
            label_template(row),
            xy=(row["year"], row[y_col]),
            xytext=(offset, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=GROUP_COLORS.get(row.get("group_name"), PALETTE.get(row.get("mother_background_group"), "black")),
        )


def _add_figure_note(fig: plt.Figure, note: str) -> None:
    fig.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8, color="#444444")


def _clean_legend(ax, *, title: str = "") -> None:
    handles, labels = ax.get_legend_handles_labels()
    filtered = [
        (handle, label)
        for handle, label in zip(handles, labels)
        if label not in {"model_label", "period", "mother_background_group", "share_type"}
    ]
    if filtered:
        new_handles, new_labels = zip(*filtered)
        ax.legend(new_handles, new_labels, loc="upper left", bbox_to_anchor=(1.01, 1), title=title)


def _plot_population_count(population_all: pd.DataFrame) -> None:
    groups = ["Danish origin", "Western immigrant origin", "Non-western immigrant origin"]
    df = population_all[population_all["group_name"].isin(groups)]
    latest = df[df["year"] == df["year"].max()]
    latest_total = latest["total_population"].iloc[0]
    latest_imm = population_all[
        (population_all["year"] == df["year"].max()) & (population_all["group_name"] == "Immigrant-origin total")
    ].iloc[0]
    fig, (ax, ax_zoom) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [2.2, 1]}, sharex=True)
    sns.lineplot(data=df, x="year", y="population", hue="group_name", palette=GROUP_COLORS, marker="o", ax=ax)
    _format_millions_axis(ax)
    ax.set_title("Population count over time by ancestry/origin group")
    ax.set_ylabel("Population")
    ax.set_xlabel("")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _direct_line_labels(ax, df, "population", lambda row: f"{row['group_name']}: {_millions(row['population'])}")
    box = (
        f"Latest year: {int(latest['year'].max())}\n"
        f"Total population: {_millions(latest_total)}\n"
        f"Immigrant-origin total: {_millions(latest_imm['population'])}\n"
        f"Immigrant-origin share: {_pct(latest_imm['population_share'])}"
    )
    ax.text(0.02, 0.08, box, transform=ax.transAxes, fontsize=11, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9})
    zoom_df = df[df["group_name"].isin(["Western immigrant origin", "Non-western immigrant origin"])]
    sns.lineplot(data=zoom_df, x="year", y="population", hue="group_name", palette=GROUP_COLORS, marker="o", ax=ax_zoom, legend=False)
    _format_millions_axis(ax_zoom)
    ax_zoom.set_title("Zoom: western and non-western immigrant-origin groups")
    ax_zoom.set_ylabel("Population")
    ax_zoom.set_xlabel("Year")
    _direct_line_labels(ax_zoom, zoom_df, "population", lambda row: f"{_millions(row['population'])}")
    save_figure(fig, OUTDIR / "01_population_count_over_time.png")


def _plot_population_share(population_all: pd.DataFrame, changes: pd.DataFrame, milestones: pd.DataFrame) -> None:
    df = population_all[population_all["group_name"].isin(GROUP_COLORS)]
    fig, ax = plt.subplots(figsize=(16, 9))
    sns.lineplot(data=df, x="year", y="population_share", hue="group_name", palette=GROUP_COLORS, marker="o", ax=ax)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title(
        "Population share over time by ancestry/origin group\n"
        "Direct labels show latest observed shares; callouts show long-run percentage-point change."
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Population share")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _direct_line_labels(ax, df, "population_share", lambda row: f"{row['group_name']}: {_pct(row['population_share'])}")
    for year in milestones["actual_year_used"].astype(int).unique():
        ax.axvline(year, color="#555555", linewidth=0.8, alpha=0.35)
        ax.text(year, ax.get_ylim()[1] * 0.98, str(year), rotation=90, va="top", ha="right", fontsize=9, color="#555555")
    latest_period = changes[changes["period"] == "2000 to latest"]
    danish_change = latest_period[latest_period["group_name"] == "Danish origin"]["change_percentage_points"].iloc[0]
    immigrant_change = latest_period[latest_period["group_name"] == "Immigrant-origin total"]["change_percentage_points"].iloc[0]
    insight = (
        f"Danish-origin share changed by {_pp(danish_change)} since the nearest 2000 milestone.\n"
        f"Immigrant-origin total changed by {_pp(immigrant_change)} over the same period."
    )
    ax.text(0.02, 0.08, insight, transform=ax.transAxes, fontsize=11, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.92})
    save_figure(fig, OUTDIR / "02_population_share_over_time.png")


def _plot_stacked_share(population_features: pd.DataFrame, milestones: pd.DataFrame) -> None:
    order = ["Danish origin", "Western immigrant origin", "Non-western immigrant origin"]
    pivot = (
        population_features[population_features["group_name"].isin(order)]
        .pivot(index="year", columns="group_name", values="population_share")
        .reindex(columns=order)
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.stackplot(pivot.index, [pivot[col] for col in order], labels=order, colors=[GROUP_COLORS[col] for col in order], alpha=0.9)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim(0, 1)
    ax.set_title("100% stacked population composition by ancestry/origin group")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of population")
    for year in milestones["actual_year_used"].astype(int).unique():
        ax.axvline(year, color="white", linewidth=1.5, alpha=0.85)
        ax.text(year, 0.98, str(year), rotation=90, va="top", ha="right", fontsize=9, color="#333333")
    latest_year = pivot.index.max()
    cumulative = 0
    for group in order:
        share = pivot.loc[latest_year, group]
        ax.text(latest_year + 0.4, cumulative + share / 2, f"{group}: {_pct(share)}", va="center", fontsize=10, color=GROUP_COLORS[group])
        cumulative += share
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    _add_figure_note(fig, "Shares are based on ancestry/origin grouping, not citizenship.")
    save_figure(fig, OUTDIR / "03_population_share_100pct_stacked_area.png")


def _plot_milestones(milestone_table: pd.DataFrame) -> None:
    groups = ["Danish origin", "Western immigrant origin", "Non-western immigrant origin", "Immigrant-origin total"]
    df = milestone_table[milestone_table["group_name"].isin(groups)].copy()
    df["milestone"] = df["milestone_label"].astype(str) + "\n(" + df["actual_year_used"].astype(str) + ")"
    fig, (ax_share, ax_count) = plt.subplots(1, 2, figsize=(18, 8))
    sns.barplot(data=df, x="milestone", y="population_share", hue="group_name", palette=GROUP_COLORS, ax=ax_share)
    ax_share.yaxis.set_major_formatter(PercentFormatter(1))
    ax_share.set_title("Population shares")
    ax_share.set_xlabel("")
    ax_share.set_ylabel("Share")
    for container in ax_share.containers:
        ax_share.bar_label(container, labels=[_pct(v.get_height()) for v in container], fontsize=8, padding=2)
    sns.barplot(data=df, x="milestone", y="population", hue="group_name", palette=GROUP_COLORS, ax=ax_count)
    _format_millions_axis(ax_count)
    ax_count.set_title("Population counts")
    ax_count.set_xlabel("")
    ax_count.set_ylabel("Population")
    for container in ax_count.containers:
        ax_count.bar_label(container, labels=[_millions(v.get_height()) if v.get_height() > 0 else "" for v in container], fontsize=8, padding=2)
    ax_share.legend_.remove()
    ax_count.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    fig.suptitle("Population composition milestones: first available year, 2010, 2020, latest year", fontsize=18, fontweight="bold")
    save_figure(fig, OUTDIR / "04_population_milestone_comparison.png")


def _plot_model_fits(population_features: pd.DataFrame, scenarios: pd.DataFrame, metrics: pd.DataFrame, milestones: pd.DataFrame) -> None:
    observed = population_features[["year", "immigrant_origin_share"]].drop_duplicates().sort_values("year")
    latest_year = int(observed["year"].max())
    fig, ax = plt.subplots(figsize=(16, 9))
    sns.lineplot(data=observed, x="year", y="immigrant_origin_share", color=GROUP_COLORS["Immigrant-origin total"], marker="o", linewidth=3, label="Observed immigrant-origin share", ax=ax)
    plot_scenarios = scenarios[scenarios["year"] <= latest_year + 35]
    sns.lineplot(data=plot_scenarios, x="year", y="immigrant_origin_share", hue="model_label", style="period", linewidth=2, alpha=0.8, ax=ax)
    ax.axvline(latest_year + 0.5, color="black", linestyle=":", linewidth=1.5)
    ax.text(latest_year + 0.8, ax.get_ylim()[1] * 0.95, "Forecast starts after latest observed year", fontsize=10, va="top")
    for year in sorted(set([int(observed["year"].min()), 2010, 2020, latest_year])):
        nearest = _nearest_year(observed["year"].astype(int).tolist(), year)
        row = observed[observed["year"] == nearest].iloc[0]
        ax.annotate(f"{nearest}: {_pct(row['immigrant_origin_share'])}", (nearest, row["immigrant_origin_share"]), xytext=(5, 10), textcoords="offset points", fontsize=9)
    metric_text = "Model fit metrics\n" + "\n".join(
        f"{row['model_label']}: R2={row['r_squared']:.3f}, RMSE={row['rmse']:.3f}"
        for _, row in metrics.iterrows()
        if pd.notna(row["r_squared"])
    )
    metric_text += f"\nLatest observed share: {_pct(observed['immigrant_origin_share'].iloc[-1])}"
    ax.text(0.02, 0.74, metric_text, transform=ax.transAxes, fontsize=10, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.92})
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title(
        "Immigrant-origin share with scenario model fits\n"
        "Scenario models are illustrative extrapolations, not official forecasts."
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Immigrant-origin share")
    _clean_legend(ax)
    save_figure(fig, OUTDIR / "05_immigrant_origin_share_with_model_fits.png")


def _plot_threshold_forecast(scenarios: pd.DataFrame, crossings: pd.DataFrame, latest_year: int) -> None:
    fig, ax = plt.subplots(figsize=(16, 9))
    plot_scenarios = scenarios[(scenarios["year"] >= latest_year - 5) & (scenarios["year"] <= latest_year + 100)]
    sns.lineplot(data=plot_scenarios, x="year", y="immigrant_origin_share", hue="model_label", style="period", linewidth=2.5, ax=ax)
    visual_thresholds = [0.20, 0.25, 0.33, 0.50, 0.75]
    for threshold in visual_thresholds:
        ax.axhline(threshold, color="#333333", linestyle=":", linewidth=1)
        ax.text(plot_scenarios["year"].min(), threshold + 0.005, f"{threshold:.0%}", fontsize=10, color="#333333")
    crossed = crossings[crossings["threshold"].isin(visual_thresholds)].copy()
    crossed = crossed[pd.to_numeric(crossed["crossing_year"], errors="coerce").notna()]
    label_offsets = {"linear": 0.005, "logarithmic": -0.014, "logistic": 0.012}
    for _, row in crossed.iterrows():
        year = int(row["crossing_year"])
        if year > plot_scenarios["year"].max():
            continue
        ax.scatter(year, row["threshold"], s=45, color="black", zorder=4)
        ax.text(
            year + 0.5,
            row["threshold"] + label_offsets.get(row["model"], 0.004),
            f"{row['threshold']:.0%}: {year} {row['model']}",
            fontsize=8,
        )
    ax.axvspan(plot_scenarios["year"].min(), latest_year, color="#eeeeee", alpha=0.45, label="Observed period")
    ax.axvline(latest_year + 0.5, color="black", linestyle=":", linewidth=1.5)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim(0, 0.80)
    ax.set_title("Scenario threshold forecast for immigrant-origin population share")
    ax.set_xlabel("Year")
    ax.set_ylabel("Immigrant-origin share")
    ax.text(0.02, 0.04, "Crossing years depend strongly on model assumptions.", transform=ax.transAxes, fontsize=11, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9})
    _clean_legend(ax)
    save_figure(fig, OUTDIR / "05_scenario_threshold_forecast.png")


def _plot_model_comparison(population_features: pd.DataFrame, scenarios: pd.DataFrame, metrics: pd.DataFrame) -> None:
    observed = population_features[["year", "immigrant_origin_share"]].drop_duplicates().sort_values("year")
    latest_value = observed["immigrant_origin_share"].iloc[-1]
    latest_year = int(observed["year"].max())
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for ax, model_key in zip(axes, ["linear", "logarithmic", "logistic"]):
        model_df = scenarios[(scenarios["model"] == model_key) & (scenarios["year"] <= latest_year + 60)]
        metric = metrics[metrics["model"] == model_key].iloc[0]
        sns.scatterplot(data=observed, x="year", y="immigrant_origin_share", color=GROUP_COLORS["Immigrant-origin total"], s=55, ax=ax)
        sns.lineplot(data=model_df, x="year", y="immigrant_origin_share", color="#333333", linewidth=2.5, ax=ax)
        ax.axvline(latest_year + 0.5, color="black", linestyle=":", linewidth=1)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_title(metric["model_label"])
        ax.set_xlabel("Year")
        ax.set_ylabel("Immigrant-origin share" if ax is axes[0] else "")
        text = (
            f"{metric['model_assumption']}\n"
            f"R2: {metric['r_squared']:.3f}\n"
            f"RMSE: {metric['rmse']:.3f}\n"
            f"Latest observed: {_pct(latest_value)}"
        )
        ax.text(0.04, 0.95, text, transform=ax.transAxes, va="top", fontsize=10, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.92})
    fig.suptitle("Model comparison: linear, logarithmic, logistic\nNot an official projection", fontsize=17, fontweight="bold")
    save_figure(fig, OUTDIR / "07_model_comparison_linear_log_logistic.png")


def _plot_birth_share(births_summary: pd.DataFrame, milestones: pd.DataFrame) -> None:
    if births_summary.empty:
        return
    df = births_summary[births_summary["mother_background_group"] != "Unknown mother background"]
    palette = {name: PALETTE[name] for name in df["mother_background_group"].unique() if name in PALETTE}
    fig, ax = plt.subplots(figsize=(16, 8))
    sns.lineplot(data=df, x="year", y="birth_share", hue="mother_background_group", palette=palette, marker="o", ax=ax)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Share of live births by mother's ancestry/background")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of live births")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    latest_year = df["year"].max()
    for _, row in df[df["year"] == latest_year].iterrows():
        ax.annotate(f"{row['mother_background_group']}: {_pct(row['birth_share'])}", (row["year"], row["birth_share"]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=10, color=palette.get(row["mother_background_group"], "black"))
    for target in [int(df["year"].min()), 2010, 2020, int(latest_year)]:
        nearest = _nearest_year(df["year"].astype(int).unique().tolist(), target)
        ax.axvline(nearest, color="#555555", linewidth=0.8, alpha=0.25)
    _add_figure_note(fig, "Births are grouped by mother's background. This is not necessarily the child's final ancestry classification.")
    save_figure(fig, OUTDIR / "08_birth_share_by_mothers_background.png")


def _plot_birth_vs_population(births_summary: pd.DataFrame, milestones: pd.DataFrame) -> None:
    if births_summary.empty:
        return
    comparable = births_summary.dropna(subset=["corresponding_population_share"]).copy()
    if comparable.empty:
        return
    available_years = comparable["year"].astype(int).unique().tolist()
    selected_years = sorted(set(_nearest_year(available_years, int(row["actual_year_used"])) for _, row in milestones.iterrows()))
    df = comparable[comparable["year"].isin(selected_years)].copy()
    df["milestone"] = df["year"].astype(str)
    long = df.melt(
        id_vars=["year", "milestone", "mother_background_group"],
        value_vars=["corresponding_population_share", "birth_share"],
        var_name="share_type",
        value_name="share",
    )
    long["share_type"] = long["share_type"].map(
        {
            "corresponding_population_share": "Population share",
            "birth_share": "Birth share by mother's background",
        }
    )
    grid = sns.catplot(
        data=long,
        x="milestone",
        y="share",
        hue="share_type",
        col="mother_background_group",
        kind="bar",
        height=5,
        aspect=1.1,
        sharey=True,
    )
    for ax in grid.axes.flat:
        ax.set_title(ax.get_title().replace("mother_background_group = ", ""))
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        for container in ax.containers:
            ax.bar_label(container, labels=[_pct(v.get_height()) for v in container], fontsize=8, padding=2)
        ax.set_xlabel("Year")
        ax.set_ylabel("Share")
    grid.fig.suptitle("Birth share vs population share at milestone years", y=1.08, fontsize=16, fontweight="bold")
    if grid._legend is not None:
        grid._legend.set_title("")
    grid.fig.text(
        0.02,
        0.01,
        "If birth share exceeds population share, this group is overrepresented among births relative to its population share.\n"
        + FOOTNOTE_DEATHS,
        ha="left",
        va="bottom",
        fontsize=8,
    )
    grid.fig.savefig(OUTDIR / "09_birth_share_vs_population_share.png", dpi=300, bbox_inches="tight")
    plt.close(grid.fig)


def _plot_birth_population_ratio(births_summary: pd.DataFrame) -> None:
    if births_summary.empty:
        return
    df = births_summary.dropna(subset=["birth_population_ratio"]).copy()
    if df.empty:
        return
    palette = {name: PALETTE[name] for name in df["mother_background_group"].unique() if name in PALETTE}
    fig, ax = plt.subplots(figsize=(16, 8))
    sns.lineplot(data=df, x="year", y="birth_population_ratio", hue="mother_background_group", palette=palette, marker="o", ax=ax)
    ax.axhline(1, color="black", linestyle=":", linewidth=1.5)
    ax.set_title("Birth-population ratio by mother's background")
    ax.set_xlabel("Year")
    ax.set_ylabel("Birth share / population share")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title="")
    latest_year = df["year"].max()
    for _, row in df[df["year"] == latest_year].iterrows():
        ax.annotate(f"{row['birth_population_ratio']:.2f}x", (row["year"], row["birth_population_ratio"]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=10, color=palette.get(row["mother_background_group"], "black"))
    ax.text(0.02, 0.07, "1.0 means birth share equals population share.\nAbove 1.0 means a higher share of births than population share.", transform=ax.transAxes, fontsize=11, bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.92})
    _add_figure_note(fig, FOOTNOTE_DEATHS)
    save_figure(fig, OUTDIR / "10_birth_population_ratio.png")


def create_hypothesis_01_plots(population_features: pd.DataFrame, births_long: pd.DataFrame | None = None) -> pd.DataFrame:
    set_theme()
    _clean_h1_output_dir()
    REPORTS_TABLES.mkdir(parents=True, exist_ok=True)

    population_features = _extended_population_features(population_features)
    if population_features.empty:
        return pd.DataFrame()

    population_all = _population_with_immigrant_total(population_features)
    milestones = _milestone_years(population_features)
    milestone_table = _build_population_milestone_table(population_all, milestones)
    changes = _build_population_changes(population_all, milestones)
    scenarios, metrics, crossings = _build_scenarios(population_features)

    milestone_table.to_csv(REPORTS_TABLES / "hypothesis_01_population_milestones.csv", index=False)
    changes.to_csv(REPORTS_TABLES / "hypothesis_01_population_changes.csv", index=False)
    crossings.to_csv(REPORTS_TABLES / "hypothesis_01_threshold_crossing_years.csv", index=False)
    _write_notes(population_features, pd.DataFrame(), milestones)

    _plot_population_count(population_all)
    _plot_population_share(population_all, changes, milestones)
    _plot_stacked_share(population_features, milestones)
    _plot_milestones(milestone_table)
    if not scenarios.empty:
        _plot_threshold_forecast(scenarios, crossings, int(population_features["year"].max()))
    return crossings
