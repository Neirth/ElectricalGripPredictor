import torch
import numpy as np
from torch.utils.data import Dataset
from preprocessors.electrical_grid import electrical_grid_preprocessor, create_daily_sliding_windows

class ElectricalGridDataset(Dataset):
    def __init__(self, data_file, device):
        # Preprocesamos el dataset utilizando la función de preprocesamiento proporcionada
        self.df = electrical_grid_preprocessor(data_file)
        self.df = create_daily_sliding_windows(self.df, 19)

        # Import the device into the dataset
        self.device = device

        # Asumimos que 'window_values' y 'window_timestamps' son listas de listas o secuencias
        self.window_values = self.df['window_values'].tolist()
        self.day_sin = self.df['day_sin'].tolist()
        self.minute_sin = self.df['minute_sin'].tolist()
        self.next_values = self.df['next_value'].tolist()

        # Convertimos las listas en arreglos numpy con la forma correcta
        self.window_values = np.array(self.window_values, dtype=np.float32)  # Cada fila puede ser una secuencia
        self.day_sin = np.array(self.day_sin, dtype=np.int64)
        self.minute_sin = np.array(self.minute_sin, dtype=np.int64)
        self.next_values = np.array(self.next_values, dtype=np.float32)

        # Aquí creamos una nueva estructura que combine los tres componentes para cada ventana deslizante
        self.combined_features = []
        for i in range(len(self.window_values)):
            # Para cada ventana, concatenamos las tres características (día, minuto y valor)
            combined_window = np.stack((
                self.day_sin[i] * np.ones_like(self.window_values[i]),  # Replicamos day_sin para cada paso de la ventana
                self.minute_sin[i],  # Minute_sin cambia en cada paso
                self.window_values[i]  # Los valores reales de la ventana
            ), axis=-1)  # Axis -1 para que sea (seq_length, 3)
            self.combined_features.append(combined_window)

        # Convertimos combined_features a un tensor directamente
        self.combined_features = np.array(self.combined_features, dtype=np.float32)

    def __len__(self):
        return len(self.next_values)

    def __getitem__(self, idx):
        # Obtenemos la secuencia combinada de features (day_sin, minute_sin, window_value) y el valor siguiente
        window_stack = torch.tensor(self.combined_features[idx], dtype=torch.float32).to(self.device)
        next_value = torch.tensor(self.next_values[idx], dtype=torch.float32).to(self.device)

        # Devolvemos los inputs (ventana combinada) y los next_values como output
        return {
            'window_stack': window_stack,
            'next_value': next_value
        }