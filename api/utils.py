import re
import pandas as pd
from enum import Enum


class Operator(str, Enum):
    """Enum for associating equality operators with a string."""
    lt = 'lt'
    lte = 'lte'
    eq = 'eq'
    gt = 'gt'
    gte = 'gte'


def convert_usd_columns(df) -> pd.DataFrame:
    """Converts any column in the DataFrame containing USD-formatted strings (like "$1,234.56")
        to float values. Ignores non-object columns.

    Args:
        - df (pd.DataFrame): The DataFrame to process

    Returns:
        - pd.DataFrame: The DataFrame with USD-formatted strings converted to floats
    """
    def is_usd_column(series: pd.Series) -> bool:
        """Checks if a column contains USD-formatted strings.
        
        Args:
            - series (pd.Series): The column to check
            
        Returns:
            - bool: True if the column contains USD-formatted strings, False otherwise
        """
        return series.astype(str).str.contains(r'\$', na=False).any()

    def parse_usd(value: str) -> float | None:
        """Converts a USD-formatted string to a float. Returns None for invalid formats.
        
        Args:
            - value (str): The USD-formatted string to convert
        
        Returns:
            - float | None: The converted float value, or None if the format is invalid
        """
        if pd.isna(value):
            return None
        clean_value = re.sub(r'[\$,]', '', str(value))
        try:
            return float(clean_value)
        except ValueError:
            return None

    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object and is_usd_column(df[col]):
            df[col] = df[col].apply(parse_usd)
    return df


def get_sheets_data(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Fetch data from a given Google Sheet sheet_id and sheet_name.
    
    Args:
        - sheet_id (str): The ID of the Google Sheet
        - sheet_name (str): The name of the sheet within the Google Sheet
        
    Returns:
        - pd.DataFrame: The data from the specified sheet as a DataFrame
    """
    sheet_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    df = pd.read_csv(sheet_url)
    df = convert_usd_columns(df)
    return df
