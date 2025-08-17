import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import StrMethodFormatter
import mplcursors
import plotly.express as px



plt.style.use('ggplot')  

def enable_hover(ax, fmt="{x}: {y:,.0f}"):
    cursor = mplcursors.cursor(ax, hover=True)
    @cursor.connect("add")
    def _(sel):
        x, y = sel.target
        sel.annotation.set_text(fmt.format(x=int(x), y=y))


def _thousands(ax):
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

def _annotate_bars(ax):
    for p in ax.patches:
        h = p.get_height()
        if np.isfinite(h):
            ax.annotate(f"{h:,.0f}", (p.get_x()+p.get_width()/2, h),
                        ha='center', va='bottom', fontsize=9,
                        xytext=(0, 4), textcoords='offset points')

def plot_avg_income_bars_last_year_pretty(df_avg, title="Średni dochód na osobę – ostatni rok", flag_path=None, ):
    if df_avg.empty:
        print("⚠️ Brak danych do wykresu."); return
    last = df_avg.index.max()
    vals = df_avg.loc[last].dropna()

    fig, ax = plt.subplots(figsize=(9,5))
    bars = ax.bar(vals.index, vals.values)

    _thousands(ax)
    _annotate_bars(ax)
    ax.set_title(f"{title} ({last})")
    ax.set_ylabel("DKK na osobę")
    ax.grid(axis='y', linestyle='--', alpha=0.35)
    fig.tight_layout()

    # 🇩🇰 flaga nad słupkiem Duńczyków
    try:
        import os
        if flag_path and os.path.exists(flag_path) and "DANSK" in vals.index:
            from matplotlib.offsetbox import OffsetImage, AnnotationBbox
            import matplotlib.image as mpimg
            idx = list(vals.index).index("DANSK")
            bar = bars[idx]
            img = mpimg.imread(flag_path)
            oi = OffsetImage(img, zoom=0.08)  # dopasuj rozmiar
            ab = AnnotationBbox(
                oi,
                (bar.get_x() + bar.get_width()/2, bar.get_height()),
                xybox=(0, 18),
                xycoords='data',
                boxcoords=("offset points"),
                frameon=False
            )
            ax.add_artist(ab)
        elif "DANSK" in vals.index:
            # awaryjnie — emoji w labelu
            new_labels = [("🇩🇰 " + x) if x=="DANSK" else x for x in vals.index]
            ax.set_xticklabels(new_labels)
    except Exception:
        pass
    enable_hover(ax)
    plt.show()


def plot_avg_income_grouped_bars_pretty(df_avg, title="Średni dochód na osobę – wg pochodzenia"):
    if df_avg.empty:
        print("⚠️ Brak danych do wykresu."); return
    years  = df_avg.index.values
    groups = df_avg.columns.tolist()
    x = np.arange(len(years))
    width = 0.25 if len(groups)==3 else 0.8/max(1,len(groups))

    fig, ax = plt.subplots(figsize=(12,6))
    for i, g in enumerate(groups):
        ax.bar(x + (i - (len(groups)-1)/2)*width, df_avg[g].values, width, label=("🇩🇰 DANSK" if g=="DANSK" else g))

    _thousands(ax)
    ax.set_xticks(x); ax.set_xticklabels(years)
    ax.set_title(title); ax.set_xlabel("Rok"); ax.set_ylabel("DKK na osobę")
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.35)
    fig.tight_layout()
    enable_hover(ax)
    plt.show()


def plot_history_with_forecast(df_hist, df_fc, title="Średni dochód – historia + prognoza", ):
    if df_hist.empty:
        print("⚠️ Brak danych historycznych."); return
    fig, ax = plt.subplots(figsize=(12,6))

    # historia: linie ciągłe
    for col in df_hist.columns:
        ax.plot(df_hist.index, df_hist[col], marker='o', label=col, linewidth=2)

    # forecast: linie przerywane
    if df_fc is not None and not df_fc.empty:
        for col in df_fc.columns:
            ax.plot(df_fc.index, df_fc[col], linestyle='--', marker='o', label=f"{col} (prognoza)", linewidth=2)

        # pionowa kreska oddzielająca
        ax.axvline(df_hist.index.max()+0.5, color='k', linestyle=':', alpha=0.5)

    _thousands(ax)
    ax.set_title(title); ax.set_xlabel("Rok"); ax.set_ylabel("DKK na osobę")
    ax.grid(True, alpha=0.3); ax.legend()
    fig.tight_layout()\
    
    enable_hover(ax)
    plt.show()



def plot_income_contribution_pie(df_totals):
    last = df_totals.index.max()
    vals = df_totals.loc[last].dropna()
    labels = vals.index
    sizes  = vals.values
    fig, ax = plt.subplots(figsize=(7,7))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.8)
    ax.set_title(f'Udział w łącznym dochodzie opodatkowanym ({last})')
    plt.show()


def plotly_income_contribution_pie(df_totals):
    last = df_totals.index.max()
    s = df_totals.loc[last].dropna()
    fig = px.pie(
        values=s.values, names=s.index,
        title=f'Udział w łącznym dochodzie opodatkowanym ({last})',
        hole=0.35
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.show()  