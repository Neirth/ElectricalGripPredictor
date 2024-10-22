# Preprocessor function using Pandas DataFrame
from pandas import DataFrame, read_csv, to_datetime, to_numeric

import numpy as np
from pandas import DataFrame, to_datetime

def create_daily_sliding_windows(df: DataFrame, window_size: int) -> DataFrame:
    """Creates sliding windows grouped by day, including the timestamp, the next value, and the sinusoidal components."""

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
    df['TIMESTAMP'] = to_datetime(df['TIMESTAMP'], format='%d/%m/%y %H:%M').astype(int)

    # Remove rows that have values of 0 in all columns except the first one
    df = df[(df.iloc[:, 1:] != 0).any(axis=1)]

    # Remove columns that have values of 0 in all their rows
    df = df.loc[:, (df != 0).any(axis=0)]

    # Replace commas with periods in all columns from the first column onward
    df.iloc[:, 1:] = df.iloc[:, 1:].replace(',', '.', regex=True)

    # Convert the values in the columns to numeric (float), ignoring errors
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(to_numeric, errors='coerce')

    # Calculate the median of each row (except the first column) and store it in a new column called global_load
    df['GLOBAL_LOAD_TOTAL'] = df.iloc[:, 1:].sum(axis=1).div(1000)

    # Make sure there are no NaN values before converting to tensor
    df = df.dropna()

    print("[*] Tail of the preprocessed dataset:")
    print(df.tail())

    df = df[['TIMESTAMP', 'GLOBAL_LOAD_TOTAL']].copy()

    return df