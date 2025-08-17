import pandas as pd
from datetime import datetime

from dansk_statistik import (
    load_INDKP109,
    clean_indkp109,
    summarize_last_year,
    forecast_linear,          # <-- z model.py
    plot_avg_income_bars_last_year_pretty,
    plot_avg_income_grouped_bars_pretty,
    plot_history_with_forecast)

def main():
    current_year = datetime.now().year - 1
    print(f"Debuguję INDKP109 do roku {current_year}\n")

    # 1) Dane per capita z INDKP109 (ENHED=121 w loaderze)
    df_raw = load_INDKP109(current_year)
    if df_raw.empty:
        print("⚠️ Brak danych z API (df_raw empty)."); return

    df_avg = clean_indkp109(df_raw)  # index=TID (int), columns=[DANSK, IND_VEST, IND_ANDRE]
    if df_avg.empty:
        print("⚠️ Brak danych po czyszczeniu (df_avg empty)."); return

    print(df_avg.tail())

    # 2) Podsumowanie ostatniego roku
    summary = summarize_last_year(df_avg)
    print("\nPodsumowanie ostatniego roku:\n", summary)

    # 3) Wizualizacje
    plot_avg_income_bars_last_year_pretty(df_avg, flag_path="assets/flags/dk.png")
    plot_avg_income_grouped_bars_pretty(df_avg)

    # 4) Prognozy: 10 lat i 5 lat
    df_fc10 = forecast_linear(df_avg, horizon=10, clip_min=0)
    df_fc5  = forecast_linear(df_avg, horizon=5,  clip_min=0)

    print("\nPrognoza 10 lat:\n", df_fc10.head())
    print("\nPrognoza 5 lat:\n", df_fc5.head())

    # 5) Wykres historia + prognoza 10 lat
    plot_history_with_forecast(df_avg, df_fc10)

    

if __name__ == "__main__":
    main()
