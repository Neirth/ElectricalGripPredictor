import torch
import numpy as np
from torch.utils.data import Dataset
from preprocessors.electrical_grid import electrical_grid_preprocessor, create_daily_sliding_windows

class ElectricalGridDataset(Dataset):
    def __init__(self, data_file, device):
        # We preprocess the dataset using the provided preprocessing function
        self.df = electrical_grid_preprocessor(data_file)
        self.df = create_daily_sliding_windows(self.df, 19)

        # Import the device into the dataset
        self.device = device

        # We assume 'window_values' and 'window_timestamps' are lists of lists or sequences
        self.window_values = self.df['window_values'].tolist()
        self.day_sin = self.df['day_sin'].tolist()
        self.minute_sin = self.df['minute_sin'].tolist()
        self.next_values = self.df['next_value'].tolist()

        # We convert the lists to numpy arrays with the correct shape
        self.window_values = np.array(self.window_values, dtype=np.float32)  # Each row can be a sequence
        self.day_sin = np.array(self.day_sin, dtype=np.int64)
        self.minute_sin = np.array(self.minute_sin, dtype=np.int64)
        self.next_values = np.array(self.next_values, dtype=np.float32)

        # Here we create a new structure that combines the three components for each sliding window
        self.combined_features = []
        for i in range(len(self.window_values)):
            # For each window, we concatenate the three features (day, minute, and value)
            combined_window = np.stack((
                self.day_sin[i] * np.ones_like(self.window_values[i]),  # We replicate day_sin for each step of the window
                self.minute_sin[i],  # Minute_sin changes at each step
                self.window_values[i]  # The actual values of the window
            ), axis=-1)  # Axis -1 so that it is (seq_length, 3)
            self.combined_features.append(combined_window)

        # We convert combined_features to a tensor directly
        self.combined_features = np.array(self.combined_features, dtype=np.float32)

    def __len__(self):
        return len(self.next_values)

    def __getitem__(self, idx):
        # We get the combined feature sequence (day_sin, minute_sin, window_value) and the next value
        window_stack = torch.tensor(self.combined_features[idx], dtype=torch.float32).to(self.device)
        next_value = torch.tensor(self.next_values[idx], dtype=torch.float32).to(self.device)

        # We return the inputs (combined window) and the next_values as output
        return {
            'window_stack': window_stack,
            'next_value': next_value
        }