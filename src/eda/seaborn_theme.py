from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

GROUP_COLORS = {
    "Danish origin": "#174A7E",
    "Western immigrant origin": "#1B7F3A",
    "Non-western immigrant origin": "#B85C1E",
    "Immigrant-origin total": "#9467bd",
}

PALETTE = {
    **GROUP_COLORS,
    "Immigrant-background mother proxy": "#9467bd",
    "Mother of Danish origin": "#1f77b4",
    "Mothers with immigrant background": "#9467bd",
    "Immigrant mother": "#9467bd",
    "Descendant mother": "#9467bd",
    "Unknown mother background": "#7f7f7f",
    "Danish citizenship": "#1f77b4",
    "Foreign citizenship": "#9467bd",
}


def set_theme() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.titlesize": 15,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def annotate_latest(ax, df, x_col: str, y_col: str, label_col: str) -> None:
    if df.empty:
        return
    latest_year = df[x_col].max()
    latest = df[df[x_col] == latest_year]
    for _, row in latest.iterrows():
        ax.annotate(
            f"{row[label_col]}\n{row[y_col]:.1%}" if 0 <= row[y_col] <= 1.5 else f"{row[label_col]}\n{row[y_col]:,.0f}",
            (row[x_col], row[y_col]),
            textcoords="offset points",
            xytext=(8, 0),
            va="center",
            fontsize=9,
        )
