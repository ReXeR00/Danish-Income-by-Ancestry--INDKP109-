
import pandas as pd
import numpy as np

def summarize_last_year(df_avg: pd.DataFrame) -> pd.DataFrame:
    """Tabela podsumowująca ostatni rok: wartości, różnice i relacje względem Duńczyków."""
    last = df_avg.index.max()
    row = df_avg.loc[last].copy()
    base = row.get('DANSK', np.nan)
    out = pd.DataFrame({
        'DKK_per_person': row,
        'Delta_vs_DANSK': row - base,
        'Ratio_vs_DANSK': row / base
    })
    out.index.name = f"{last}"
    return out.sort_values('DKK_per_person', ascending=False)

def rolling_mean(df_avg: pd.DataFrame, window:int=3) -> pd.DataFrame:
    """Wygładzenie 3-letnią średnią kroczącą (domyślnie)."""
    return df_avg.sort_index().rolling(window=window, min_periods=1).mean()

def yoy_change(df_avg: pd.DataFrame) -> pd.DataFrame:
    """Zmiana r/r w %."""
    return df_avg.sort_index().pct_change()*100

def to_index_base(df_avg: pd.DataFrame, base_year:int) -> pd.DataFrame:
    """Przelicza każdy szereg na indeks = 100 w roku bazowym."""
    base = df_avg.loc[base_year]
    return (df_avg / base) * 100

# Prosty forecast liniowy na 3 lata do przodu (sklearn)
from sklearn.linear_model import LinearRegression

def forecast_linear(df_avg: pd.DataFrame, horizon:int=3) -> pd.DataFrame:
    """
    Prosty model: dla każdej grupy regresja liniowa po czasie (rok -> DKK/os),
    zwraca DataFrame z prognozą na kolejne 'horizon' lat.
    """
    years = df_avg.index.values.reshape(-1, 1)
    future_years = np.arange(df_avg.index.max()+1, df_avg.index.max()+1+horizon).reshape(-1,1)
    fc = pd.DataFrame(index=future_years.ravel(), columns=df_avg.columns, dtype=float)

    for col in df_avg.columns:
        y = df_avg[col].values
        if np.isfinite(y).sum() >= 2:  # minimalnie 2 punkty
            m = LinearRegression()
            m.fit(years, y)
            fc[col] = m.predict(future_years)
    fc.index.name = "TID"
    return fc