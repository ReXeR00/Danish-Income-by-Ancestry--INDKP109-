import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

EN = {
    "title_last": "Average income per person — last year",
    "title_grouped": "Average income per person — by ancestry",
    "ylabel_dkk": "DKK per person",
    "forecast_suffix": "(forecast)",
    "groups": {
        "DANSK": "Danes",
        "IND_VEST": "Western immigrants",
        "IND_ANDRE": "Non-western immigrants",
    },
}

def _rename_groups(df):
    return df.rename(columns=EN["groups"])

def _format_thousands(ax):
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

def _annotate_bars(ax):
    for p in ax.patches:
        h = p.get_height()
        if np.isfinite(h):
            ax.annotate(
                f"{h:,.0f}",
                (p.get_x() + p.get_width() / 2, h),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 4),
                textcoords="offset points",
            )

def plot_avg_income_bars_last_year_pretty(df_avg, title=None, flag_path=None):
    """Bar chart for the latest year (English labels only)."""
    if df_avg is None or df_avg.empty:
        print("⚠️ No data."); return
    df_loc = _rename_groups(df_avg)
    last = df_loc.index.max()
    vals = df_loc.loc[last].dropna()

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(vals.index, vals.values)

    _format_thousands(ax)
    _annotate_bars(ax)
    ax.set_title(title or f"{EN['title_last']} ({last})")
    ax.set_ylabel(EN["ylabel_dkk"])
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()

    # Optional 🇩🇰 flag over Danes bar (works if flag file exists)
    try:
        if flag_path:
            import os
            if os.path.exists(flag_path) and "Danes" in vals.index:
                from matplotlib.offsetbox import OffsetImage, AnnotationBbox
                import matplotlib.image as mpimg
                idx = list(vals.index).index("Danes")
                bar = bars[idx]
                img = mpimg.imread(flag_path)
                oi = OffsetImage(img, zoom=0.08)
                ab = AnnotationBbox(
                    oi,
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xybox=(0, 18),
                    xycoords="data",
                    boxcoords=("offset points"),
                    frameon=False,
                )
                ax.add_artist(ab)
    except Exception:
        pass

    plt.show()

def plot_avg_income_grouped_bars_pretty(df_avg, title=None):
    """Grouped bars over years (English labels only)."""
    if df_avg is None or df_avg.empty:
        print("⚠️ No data."); return
    df_loc = _rename_groups(df_avg)
    years = df_loc.index.values
    groups = df_loc.columns.tolist()
    x = np.arange(len(years))
    width = 0.25 if len(groups) == 3 else 0.8 / max(1, len(groups))

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, g in enumerate(groups):
        ax.bar(x + (i - (len(groups) - 1) / 2) * width, df_loc[g].values, width, label=g)

    _format_thousands(ax)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_title(title or EN["title_grouped"])
    ax.set_xlabel("Year")
    ax.set_ylabel(EN["ylabel_dkk"])
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    plt.show()

def plot_history_with_forecast(df_hist, df_fc, title=None):
    """History + forecast (English labels only)."""
    if df_hist is None or df_hist.empty:
        print("⚠️ No historical data."); return

    dfh = _rename_groups(df_hist)
    dfc = _rename_groups(df_fc) if (df_fc is not None and not df_fc.empty) else None

    fig, ax = plt.subplots(figsize=(12, 6))
    for col in dfh.columns:
        ax.plot(dfh.index, dfh[col], marker="o", label=col, linewidth=2)

    if dfc is not None:
        for col in dfc.columns:
            ax.plot(dfc.index, dfc[col], linestyle="--", marker="o", label=f"{col} {EN['forecast_suffix']}", linewidth=2)
        ax.axvline(dfh.index.max() + 0.5, color="k", linestyle=":", alpha=0.5)

    _format_thousands(ax)
    ax.set_title(title or "Average income — history + forecast")
    ax.set_xlabel("Year")
    ax.set_ylabel(EN["ylabel_dkk"])
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    plt.show()
