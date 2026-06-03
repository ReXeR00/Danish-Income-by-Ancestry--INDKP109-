from __future__ import annotations

import numpy as np
import pandas as pd

from .trend_models import (
    fit_linear_trend,
    fit_log_trend,
    fit_logistic_trend,
    predict_linear,
    predict_log,
    predict_logistic,
)


def population_share_scenarios(population_features: pd.DataFrame, horizon: int = 80) -> tuple[pd.DataFrame, pd.DataFrame]:
    if population_features.empty:
        return pd.DataFrame(), pd.DataFrame()
    share = (
        population_features[["year", "immigrant_origin_share"]]
        .drop_duplicates()
        .dropna()
        .sort_values("year")
    )
    if len(share) < 2:
        return pd.DataFrame(), pd.DataFrame()
    max_year = int(share["year"].max())
    years = np.arange(int(share["year"].min()), max_year + horizon + 1)
    models = {
        "linear": (fit_linear_trend(share, "year", "immigrant_origin_share"), predict_linear),
        "logarithmic": (fit_log_trend(share, "year", "immigrant_origin_share"), predict_log),
        "logistic": (fit_logistic_trend(share, "year", "immigrant_origin_share"), predict_logistic),
    }
    scenario_frames = []
    threshold_rows = []
    for name, (info, predict_fn) in models.items():
        preds = predict_fn(info, years.astype(float))
        preds = np.clip(preds, 0, 1.5)
        frame = pd.DataFrame({"year": years, "model": name, "immigrant_origin_share": preds})
        scenario_frames.append(frame)
        metrics = info.get("metrics", {})
        for threshold in [0.25, 0.50, 1.00]:
            if name in {"logarithmic", "logistic"} and threshold >= 1.0:
                reached = "not meaningful"
            else:
                reached_years = frame.loc[frame["immigrant_origin_share"] >= threshold, "year"]
                reached = int(reached_years.iloc[0]) if not reached_years.empty else "not reached"
            threshold_rows.append(
                {
                    "model": name,
                    "threshold": threshold,
                    "threshold_label": f"{threshold:.0%}",
                    "threshold_year": reached,
                    "rmse": metrics.get("rmse"),
                    "mae": metrics.get("mae"),
                    "r2": metrics.get("r2"),
                }
            )
    scenarios = pd.concat(scenario_frames, ignore_index=True)
    thresholds = pd.DataFrame(threshold_rows)
    return scenarios, thresholds
