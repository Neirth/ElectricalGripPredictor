# Preprocessor function using Pandas DataFrame
from pandas import DataFrame, read_csv, to_datetime, to_numeric
from sklearn.cluster import KMeans

import numpy as np
from pandas import DataFrame, to_datetime

def create_daily_sliding_windows(df: DataFrame, window_size: int) -> DataFrame:
    """Crea ventanas deslizantes agrupadas por día, incluyendo el timestamp, el siguiente valor y los componentes sinusoidales."""

    # Convertir el TIMESTAMP a datetime para facilitar la agrupación
    df['TIMESTAMP'] = to_datetime(df['TIMESTAMP'], unit='ns')

    # Crear los componentes sinusoidales
    df['day_of_year'] = df['TIMESTAMP'].dt.dayofyear
    df['minutes_of_day'] = df['TIMESTAMP'].dt.hour * 60 + df['TIMESTAMP'].dt.minute

    # Componente sinusoidal del día en el año
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)

    # Componente sinusoidal de los minutos en el día
    df['minute_sin'] = np.sin(2 * np.pi * df['minutes_of_day'] / 1440)  # 1440 = 60 * 24 (minutos en un día)

    # Agrupar por día
    daily_groups = df.groupby(df['TIMESTAMP'].dt.date)

    windows = []

    for date, group in daily_groups:
        # Revisar si el grupo tiene suficientes datos para crear ventanas
        if len(group) > window_size:
            # Crear ventanas deslizantes para cada grupo diario
            for i in range(len(group) - window_size):
                window_values = group['GLOBAL_LOAD_MEDIAN'].iloc[i:i + window_size].values
                next_value = group['GLOBAL_LOAD_MEDIAN'].iloc[i + window_size]

                # Añadir los componentes sinusoidales a la ventana
                window_day_sin = group['day_sin'].iloc[i:i + window_size].values
                window_minute_sin = group['minute_sin'].iloc[i:i + window_size].values

                if len(window_values) == window_size:
                    windows.append((window_values, window_day_sin, window_minute_sin, next_value))
        else:
            print(f"[!] El grupo de {date} tiene menos registros que el tamaño de la ventana ({len(group)} < {window_size})")

    # Verificar si hay ventanas generadas
    if len(windows) == 0:
        print("[!] No se han generado ventanas deslizantes, revisa el tamaño de tus grupos y la ventana.")

    # Convertir la lista de ventanas a un DataFrame
    window_df = DataFrame(windows, columns=['window_values', 'day_sin', 'minute_sin', 'next_value'])

    print("[*] Datos generados a partir del dataset en crudo:")
    print(window_df.tail())

    print("[*] Conjunto de datos preprocesados a una matriz de dos columnas...")

    return window_df

def electrical_grid_preprocessor(file: str) -> DataFrame:
    # Load the data
    df = read_csv(file, on_bad_lines='skip', delimiter=";", low_memory=False)

    # Como nota, el timestamp viene en la primera columna como una cadena de texto, hay que pasarla al formato unix
    df['TIMESTAMP'] = to_datetime(df['TIMESTAMP'], format='%d/%m/%y %H:%M').astype(int)

    # Eliminamos las filas que tengan valores 0 en todas sus columnas salvo la primera
    df = df[(df.iloc[:, 1:] != 0).any(axis=1)]

    # Eliminamos las columnas que tengan valores 0 en todas sus filas
    df = df.loc[:, (df != 0).any(axis=0)]

    # Reemplaza las comas por puntos en todas las columnas a partir de la columna 1 en adelante
    df.iloc[:, 1:] = df.iloc[:, 1:].replace(',', '.', regex=True)

    # Convierte los valores de las columnas a numéricos (float), ignorando errores
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(to_numeric, errors='coerce')

    # Calculamos la mediana de cada fila (Salvo la primera columna) y la guardamos en una nueva columna llamada global_load
    df['GLOBAL_LOAD_MEDIAN'] = df.iloc[:, 1:].median(axis=1)

    # Asegúrate de que no haya NaN antes de convertir a tensor
    df = df.dropna()

    # Aplicamos el algoritmo K-Means para clasificar los valores de global_load en HIGH, MEDIUM, LOW
    kmeans = KMeans(n_clusters=3)
    kmeans.fit(df['GLOBAL_LOAD_MEDIAN'].values.reshape(-1, 1))
    df['GLOBAL_LOAD_CLASS'] = kmeans.predict(df['GLOBAL_LOAD_MEDIAN'].values.reshape(-1, 1))

    df = df[['TIMESTAMP', 'GLOBAL_LOAD_MEDIAN', 'GLOBAL_LOAD_CLASS']].copy()

    return df