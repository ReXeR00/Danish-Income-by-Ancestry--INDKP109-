# Danish Immigration & Income — StatBank DK (INDKP109)

**Status:** _Actively developed._ A larger update is planned once we obtain more detailed, country-level inputs/mappings from Statistics Denmark. For now the analysis focuses on the **three main ancestry groups**; **country-level breakdowns** are on the roadmap.

This project analyzes **average taxable income per person (DKK/person)** in Denmark across three ancestry groups:

- **Danes** (`DANSK`)
- **Western immigrants** (`IND_VEST`)
- **Non-western immigrants** (`IND_ANDRE`)

The analysis uses **StatBank Denmark** table **INDKP109** with:

- `INDKOMSTTYPE = 105` (taxable income),
- `ENHED = 121` (DKK per person — already per-capita),
- national total (`REGLAND = 000`), all ages (`ALDER1 = TOT`), both sexes (`KOEN = MOK`).

> There is scaffolding for **FOLK1C** (population by country of origin). It’s **not used** in the current pipeline yet; it will power country-level views once the detailed inputs are finalized.

---

## What’s included now

- Robust StatBank **API** calls (POST, CSV parsing)
- Clean, pivoted time series: `TID` on rows; `{DANSK, IND_VEST, IND_ANDRE}` on columns
- Last-year summary (level, delta vs Danes, ratio vs Danes)
- Rolling means, YoY changes, base-year indices
- Simple forecasts (5–10y) via time-trend models (linear / polynomial)
- Clear visuals (Matplotlib), optional hover via `mplcursors`
- Optional **contribution pie** using INDKP109 totals (`ENHED = 110`, thousand DKK)

---

## Roadmap

- **FOLK1C integration**: country-level population; West/Non-West mapping; rankings
- **Country-level income** views (once detailed mapping/data are available)
- **Contribution index** = group share of total income / group share of population
- **Exogenous drivers**: CPI (real DKK), immigration flows (VAN1AAR), employment/unemployment, GDP
- **Interactive app** (as a separate optional component)

---

## Environment

Tested with:

- **Python**: 3.11 (3.10+ should work)

**Key libraries**

- pandas 2.2.x
- numpy 1.26+
- requests 2.31+
- matplotlib 3.8+
- scikit-learn 1.5+ _(optional; forecasts fall back to `numpy.polyfit` if not installed)_
- mplcursors 0.5+ _(optional; enables hover tooltips on Matplotlib plots)_

> You can install only the minimal set (pandas, numpy, requests, matplotlib). `scikit-learn` and `mplcursors` are optional.

---

## Setup

Create a virtual environment and install dependencies manually:

```bash
# 1) Create & activate venv
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Upgrade pip
pip install -U pip

# 3) Minimal dependencies (core analysis)
pip install pandas numpy requests matplotlib

# 4) Optional extras
# Forecasts via sklearn (fallback with numpy.polyfit is used if not installed):
# pip install scikit-learn
# Hover tooltips on Matplotlib:
# pip install mplcursors
Run
Package-style layout (src/dansk_statistik/...):

bash
Kopiuj
Edytuj
python -m src.dansk_statistik.main
Flat layout (e.g., main.py next to modules):

bash
Kopiuj
Edytuj
python main.py
The script will:

fetch INDKP109 per-capita taxable income,

clean & pivot the data,

print a last-year summary,

render a bar chart (last year), grouped bars over time, and a history-with-forecast chart.

By default, it uses current_year = (today.year - 1) to avoid partially published years.

Language
The codebase and all plot labels are English-only. Legend mapping:

DANSK → Danes

IND_VEST → Western immigrants

IND_ANDRE → Non-western immigrants

StatBank query (what we ask for)
INDKP109 (current scope):

ALDER1 = TOT

REGLAND = 000

KOEN = MOK

HERKOMST ∈ {DANSK, IND_VEST, IND_ANDRE}

INDKOMSTTYPE = 105 (taxable income)

ENHED = 121 (DKK per person)

TID = 2015..latest_complete_year

Optional totals (for contribution pie):

same filters, but ENHED = 110 (thousand DKK)

FOLK1C scaffolding is present and reserved for future country-level extensions.

Notes & assumptions
Per-capita: ENHED = 121 already yields DKK/person, so no manual division is needed.

Latest year: Income data are published with a lag; we default to year − 1.

Forecasts: Simple time-trend models; results are illustrative (not official projections).

License & data attribution
Code: MIT (see LICENSE).

Data: © Statistics Denmark, StatBank Denmark. Reuse allowed under CC BY 4.0 with source attribution.
Suggested credit:

“Source: Statistics Denmark — StatBank Denmark (table INDKP109), accessed YYYY-MM-DD.”

If you publish charts, include this credit in captions or footnotes.

Contributing
PRs welcome. If you add variables (e.g., CPI deflation, employment), keep changes modular (features/, forecast/, plots/) and avoid breaking the simple main.py flow.

FAQ
Where do I change the year range?
In load_INDKP109() — adjust the TID range/list. The example uses range(2015, current_year) with current_year = datetime.now().year - 1.

I don’t have scikit-learn. Will forecasts work?
Yes. The code falls back to numpy.polyfit if scikit-learn is missing.

Hover doesn’t show up on plots.
Install mplcursors and run in an environment with GUI support (local Python, not headless CI).
```
