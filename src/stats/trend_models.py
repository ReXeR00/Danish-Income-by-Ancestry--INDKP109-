from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(y_true, y_pred)
    return {
        "rmse": float(np.sqrt(mse)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else np.nan,
    }


def fit_linear_trend(df: pd.DataFrame, x_col: str, y_col: str) -> dict[str, object]:
    clean = df[[x_col, y_col]].dropna()
    if len(clean) < 2:
        return {"model": None, "metrics": {}, "predictions": pd.DataFrame()}
    x = clean[x_col].to_numpy(dtype=float).reshape(-1, 1)
    y = clean[y_col].to_numpy(dtype=float)
    model = LinearRegression().fit(x, y)
    pred = model.predict(x)
    return {
        "model": model,
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "metrics": _metrics(y, pred),
        "predictions": clean.assign(predicted=pred),
    }


def fit_log_trend(df: pd.DataFrame, x_col: str, y_col: str) -> dict[str, object]:
    clean = df[[x_col, y_col]].dropna()
    if len(clean) < 2:
        return {"model": None, "metrics": {}, "predictions": pd.DataFrame()}
    x0 = clean[x_col].min() - 1
    x = np.log(clean[x_col].to_numpy(dtype=float) - x0).reshape(-1, 1)
    y = clean[y_col].to_numpy(dtype=float)
    model = LinearRegression().fit(x, y)
    pred = model.predict(x)
    return {
        "model": model,
        "x_offset": float(x0),
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "metrics": _metrics(y, pred),
        "predictions": clean.assign(predicted=pred),
    }


def logistic_function(x: np.ndarray, carrying_capacity: float, growth: float, midpoint: float) -> np.ndarray:
    return carrying_capacity / (1 + np.exp(-growth * (x - midpoint)))


def fit_logistic_trend(df: pd.DataFrame, x_col: str, y_col: str, ceiling: float = 1.0) -> dict[str, object]:
    clean = df[[x_col, y_col]].dropna()
    if len(clean) < 5:
        return {"model": None, "metrics": {}, "predictions": pd.DataFrame(), "warning": "not enough observations"}
    x = clean[x_col].to_numpy(dtype=float)
    y = clean[y_col].to_numpy(dtype=float)
    try:
        params, _ = curve_fit(
            logistic_function,
            x,
            y,
            p0=[min(ceiling, max(y) * 2), 0.05, np.median(x)],
            bounds=([max(y), -2, min(x) - 100], [ceiling, 2, max(x) + 300]),
            maxfev=20000,
        )
        pred = logistic_function(x, *params)
    except Exception as exc:
        return {"model": None, "metrics": {}, "predictions": pd.DataFrame(), "warning": str(exc)}
    return {
        "model": "logistic",
        "params": {"carrying_capacity": params[0], "growth": params[1], "midpoint": params[2]},
        "metrics": _metrics(y, pred),
        "predictions": clean.assign(predicted=pred),
    }


def predict_linear(model_info: dict[str, object], years: np.ndarray) -> np.ndarray:
    model = model_info.get("model")
    if model is None or not hasattr(model, "predict"):
        return np.full_like(years, np.nan, dtype=float)
    return model.predict(years.reshape(-1, 1))


def predict_log(model_info: dict[str, object], years: np.ndarray) -> np.ndarray:
    model = model_info.get("model")
    if model is None or not hasattr(model, "predict"):
        return np.full_like(years, np.nan, dtype=float)
    x_offset = float(model_info["x_offset"])
    return model.predict(np.log(years - x_offset).reshape(-1, 1))


def predict_logistic(model_info: dict[str, object], years: np.ndarray) -> np.ndarray:
    if model_info.get("model") != "logistic":
        return np.full_like(years, np.nan, dtype=float)
    params = model_info["params"]
    return logistic_function(
        years,
        float(params["carrying_capacity"]),
        float(params["growth"]),
        float(params["midpoint"]),
    )
