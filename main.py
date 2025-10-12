import pandas as pd
from datetime import datetime

from dansk_statistik import (
    load_INDKP109,
    clean_indkp109,
    summarize_last_year,
    forecast_linear,          
    plot_avg_income_bars_last_year_pretty,
    plot_avg_income_grouped_bars_pretty,
    plot_history_with_forecast)

def main():
    current_year = datetime.now().year - 1
    print(f"Debugging INDKP109 to year {current_year}\n")

    # 1) Per capita data from INDKP109 (ENHED=121 in the loader)
    df_raw = load_INDKP109(current_year)
    if df_raw.empty:
        print("⚠️ No data from API (df_raw is empty)."); return

    df_avg = clean_indkp109(df_raw)  # index=TID (int), columns=[DANSK, IND_VEST, IND_ANDRE]
    if df_avg.empty:
        print("⚠️ No data after cleaning (df_avg is empty)."); return

    print(df_avg.tail())

    # 2) Last year summary
    summary = summarize_last_year(df_avg)
    print("\nLast year summary:\n", summary)

    # 3) Visualizations
    plot_avg_income_bars_last_year_pretty(df_avg, flag_path="assets/flags/dk.png")
    plot_avg_income_grouped_bars_pretty(df_avg)

    # 4) Forecasts: 10 years and 5 years
    df_fc10 = forecast_linear(df_avg, horizon=10, clip_min=0)
    df_fc5  = forecast_linear(df_avg, horizon=5,  clip_min=0)

    print("\n10-year forecast:\n", df_fc10.head())
    print("\n5-year forecast:\n", df_fc5.head())

    # 5) Plot history + 10-year forecast
    plot_history_with_forecast(df_avg, df_fc10)

    

if __name__ == "__main__":
    main()
