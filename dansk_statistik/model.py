from __future__ import annotations
import numpy as np
import pandas as pd


try:
    from sklearn.linear_model import LinearRegression
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False


def _as_years(x_index: pd.Index) -> np.ndarray:
    """Zapewnia, że indeks to lata (float) do uczenia/predykcji."""
    years = np.asarray(x_index, dtype=float).reshape(-1, 1)
    return years


def forecast_linear(df_hist: pd.DataFrame, horizon: int = 10,
                    clip_min: float | None = None) -> pd.DataFrame:
    """
    Prosta prognoza liniowa na N lat do przodu dla każdej kolumny.
    Wejście: df_hist z indeksem = lata (int), kolumny = grupy (DANSK / IND_VEST / IND_ANDRE),
             wartości = DKK na osobę (np. z INDKP109, ENHED=121).
    Zwraca: DataFrame z indeksem = lata przyszłe, te same kolumny, wartości prognozowane.

    Parametry:
      - horizon: liczba lat do przodu (np. 10)
      - clip_min: jeżeli ustawisz np. 0, zetnie ew. ujemne predykcje do 0
    """
    if df_hist.empty:
        return pd.DataFrame()

    # lata historii i lata przyszłe
    start_next = int(df_hist.index.max()) + 1
    future_years = np.arange(start_next, start_next + horizon, dtype=int)
    X_hist = _as_years(df_hist.index)
    X_fut = future_years.reshape(-1, 1)

    fc = pd.DataFrame(index=future_years, columns=df_hist.columns, dtype=float)
    fc.index.name = "TID"

    for col in df_hist.columns:
        y = pd.to_numeric(df_hist[col], errors='coerce').values
        mask = np.isfinite(y)
        if mask.sum() < 2:
            # za mało punktów do regresji — zostaw NaN
            continue

        y_fit = y[mask]
        X_fit = X_hist[mask]

        if _HAS_SKLEARN:
            model = LinearRegression()
            model.fit(X_fit, y_fit)
            y_pred = model.predict(X_fut)
        else:
            # fallback: dopasuj prostą y = a*x + b
            coeffs = np.polyfit(X_fit.ravel(), y_fit, deg=1)
            y_pred = np.polyval(coeffs, X_fut.ravel())

        if clip_min is not None:
            y_pred = np.clip(y_pred, clip_min, None)

        fc[col] = y_pred

    return fc


def forecast_poly(df_hist: pd.DataFrame, horizon: int = 10, degree: int = 2, clip_min: float | None = None) -> pd.DataFrame:
    if df_hist.empty:
        return pd.DataFrame()

    start_next = int(df_hist.index.max()) + 1
    future_years = np.arange(start_next, start_next + horizon, dtype=int)
    X_hist = _as_years(df_hist.index).ravel()
    X_fut = future_years.astype(float)

    fc = pd.DataFrame(index=future_years, columns=df_hist.columns, dtype=float)
    fc.index.name = "TID"

    for col in df_hist.columns:
        y = pd.to_numeric(df_hist[col], errors='coerce').values
        mask = np.isfinite(y)
        if mask.sum() < degree + 1:
            continue

        coeffs = np.polyfit(X_hist[mask], y[mask], deg=max(1, degree))
        y_pred = np.polyval(coeffs, X_fut)

        if clip_min is not None:
            y_pred = np.clip(y_pred, clip_min, None)

        fc[col] = y_pred

    return fc
