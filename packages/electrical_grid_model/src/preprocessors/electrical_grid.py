# Preprocessor function using Pandas DataFrame
from pandas import DataFrame, read_csv, to_datetime, to_numeric

import numpy as np
from pandas import DataFrame, to_datetime

from sklearn.metrics import r2_score
from sklearn.preprocessing import MinMaxScaler


def calculate_r2_from_csv(file_path: str, forecast_col: str = 'LOAD_FORECAST', real_col: str = 'GLOBAL_LOAD_TOTAL') -> float:
    """
    Load a CSV file and calculate the R-squared score between two columns.

    Args:
        file_path (str): The path to the CSV file.
        forecast_col (str): Name of the column for the forecasted load. By default is 'FORECAST_LOAD'.
        real_col (str): Name of the column for the real load. By default is 'REAL_LOAD'.

    Returns:
        float: The R-squared score between the two columns.
    """
    # Load the CSV file
    df = read_csv(file_path, on_bad_lines='skip', delimiter=";", low_memory=False)

    # Ensure no NaN values in the columns
    df = df[[forecast_col, real_col]].dropna()

    # Calculate R-squared score
    r2 = r2_score(df[real_col], df[forecast_col])

    return r2

def normalize_by_year(df: DataFrame) -> DataFrame:
    """Normalizes the GLOBAL_LOAD_TOTAL by year and returns a new DataFrame."""
    # Extract the year from the TIMESTAMP for grouping
    df['TIMESTAMP'] = to_datetime(df['START_TIME'])
    df['year'] = df['TIMESTAMP'].dt.year

    # Initialize the scaler
    scaler = MinMaxScaler()

    # Create a new DataFrame with the normalized values
    normalized_df = df.copy()

    # Group by year and normalize GLOBAL_LOAD_TOTAL
    for year, group in df.groupby('year'):
        # Normalize the values for each year
        values = group['GLOBAL_LOAD_TOTAL'].values.reshape(-1, 1)
        normalized_values = scaler.fit_transform(values)

        # Replace the values in the original DataFrame
        normalized_df.loc[df['year'] == year, 'GLOBAL_LOAD_TOTAL'] = normalized_values

    # Convert the TIMESTAMP to an integer for easier processing
    normalized_df['TIMESTAMP'] = df['TIMESTAMP'].astype(int)

    # Drop the year column as it's no longer needed
    normalized_df.drop(columns=['year', 'START_TIME'], inplace=True)

    print("[*] Normalized GLOBAL_LOAD_TOTAL by year.")
    print(normalized_df.tail())

    return normalized_df


def create_daily_sliding_windows(df: DataFrame, window_size: int) -> DataFrame:
    """Creates sliding windows grouped by day, including the timestamp, the next value, and the sinusoidal components."""

    df = normalize_by_year(df)

    # Convert TIMESTAMP to datetime for easier grouping
    df['TIMESTAMP'] = to_datetime(df['TIMESTAMP'], unit='ns')

    # Create the sinusoidal components
    df['day_of_year'] = df['TIMESTAMP'].dt.dayofyear
    df['minutes_of_day'] = df['TIMESTAMP'].dt.hour * 60 + df['TIMESTAMP'].dt.minute

    # Sinusoidal component of the day in the year
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)

    # Sinusoidal component of the minutes in the day
    df['minute_sin'] = np.sin(2 * np.pi * df['minutes_of_day'] / 1440)  # 1440 = 60 * 24 (minutes in a day)

    # Group by day
    daily_groups = df.groupby(df['TIMESTAMP'].dt.date)

    windows = []

    for date, group in daily_groups:
        # Check if the group has enough data to create windows
        if len(group) > window_size:
            # Create sliding windows for each daily group
            for i in range(len(group) - window_size):
                window_values = group['GLOBAL_LOAD_TOTAL'].iloc[i:i + window_size].values
                next_value = group['GLOBAL_LOAD_TOTAL'].iloc[i + window_size]

                # Add the sinusoidal components to the window
                window_day_sin = group['day_sin'].iloc[i:i + window_size].values
                window_minute_sin = group['minute_sin'].iloc[i:i + window_size].values

                if len(window_values) == window_size:
                    windows.append((window_values, window_day_sin, window_minute_sin, next_value))
        else:
            print(f"[!] The group for {date} has fewer records than the window size ({len(group)} < {window_size})")

    # Check if any windows were generated
    if len(windows) == 0:
        print("[!] No sliding windows have been generated, check the size of your groups and the window.")

    # Convert the list of windows to a DataFrame
    window_df = DataFrame(windows, columns=['window_values', 'day_sin', 'minute_sin', 'next_value'])

    print("[*] Data generated from the raw dataset:")
    print(window_df.tail())

    print("[*] Preprocessed dataset to a two-column matrix...")

    return window_df

def electrical_grid_preprocessor(file: str) -> DataFrame:
    # Load the data
    df = read_csv(file, on_bad_lines='skip', delimiter=";", low_memory=False)

    # As a note, the timestamp comes in the first column as a string, it needs to be converted to unix format
    df['START_TIME'] = to_datetime(df['START_TIME'], format='%d/%m/%y %H:%M').astype(int)
    df['END_TIME'] = to_datetime(df['END_TIME'], format='%d/%m/%y %H:%M').astype(int)

    # Make sure there are no NaN values before converting to tensor
    df = df.dropna()

    print("[*] Tail of the preprocessed dataset:")
    print(df.tail())

    df = df[['START_TIME', 'GLOBAL_LOAD_TOTAL']].copy()

    return df