import torch
import torch.nn as nn

INPUT_SIZE = 3  # Number of features in the input
HIDDEN_SIZE = 64  # Size of hidden units in the LSTM

class GridLinearModel(nn.Module):
    def __init__(self):
        super(GridLinearModel, self).__init__()
        # LSTM with 4 layers
        self.lstm = nn.LSTM(INPUT_SIZE, HIDDEN_SIZE, 4, batch_first=True, bidirectional=False)

        # Using mean pooling to reduce the sequence
        self.fc = nn.Linear(HIDDEN_SIZE, 1)  # Final fully-connected layer

    def forward(self, x):
        # x shape: (batch_size, seq_length, input_size)
        lstm_out, _ = self.lstm(x)  # lstm_out: (batch_size, seq_length, hidden_size)

        # Compute the mean across the sequence dimension
        mean_out = torch.mean(lstm_out, dim=1)  # (batch_size, hidden_size)

        # Pass the reduced context through the fully-connected layer
        output = self.fc(mean_out)  # (batch_size, 1)

        return output