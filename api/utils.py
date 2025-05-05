import os
import pandas as pd


def get_sheets_data(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Fetch data from a given Google Sheet sheet_id and sheet_name."""
    sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    df = pd.read_csv(sheet_url)
    return df
