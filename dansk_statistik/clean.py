import pandas as pd

def clean_folk1c(df_raw):
    df_base = df_raw[['TID', 'IELAND', 'INDHOLD']].copy()
    df = df_base.dropna()
    df = df[df['TID'].str.endswith('K4')]
    df_base_pivot = df.pivot_table(
        index='TID',
        columns='IELAND',
        values='INDHOLD'
    )
    return df_base_pivot


def clean_indkp109(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw[['TID','HERKOMST','INDHOLD']].copy()
    df = df.pivot(index='TID', columns='HERKOMST', values='INDHOLD')
    df.index = df.index.astype(int)
    return df.sort_index()


def clean_indkp109_totals(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw[['TID','HERKOMST','INDHOLD']].copy()
    df = df.pivot(index='TID', columns='HERKOMST', values='INDHOLD')
    df.index = df.index.astype(int)
    return df.sort_index()