import requests
import pandas as pd
from api import STATBANK_API

def fetch_statbank_data(table_id: str, variables: dict, format: str = "CSV") -> pd.DataFrame:
    payload = {
        "table": table_id,
        "format": format,
        "valuePresentation": "Code",
        "variables": [{"code": k, "values": v} for k, v in variables.items()],
    }
    try:
        response = requests.post(STATBANK_API, json=payload, stream=True)
        response.raise_for_status()
        return pd.read_csv(response.raw, sep=';')
    except requests.exceptions.RequestException as e:
        print("Błąd API:", e)
        return pd.DataFrame()