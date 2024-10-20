import torch.nn as nn
import torch

INPUT_SIZE = 3  # Asumiendo que tienes una entradas: valores
HIDDEN_SIZE = 64

class GridLinearModel(nn.Module):
    def __init__(self):
        super(GridLinearModel, self).__init__()
        self.lstm = nn.LSTM(INPUT_SIZE, HIDDEN_SIZE, 4, batch_first=True, bidirectional=True)
        self.attention = nn.Linear(HIDDEN_SIZE * 2, 1)  # atención sobre ambas direcciones
        self.fc = nn.Linear(HIDDEN_SIZE * 2, 1)  # capa fully-connected

    def forward(self, x):
        # x shape: (batch_size, seq_length, input_size)
        lstm_out, (hn, cn) = self.lstm(x)  # lstm_out: (batch_size, seq_length, hidden_size*2)
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = torch.sum(attention_weights * lstm_out, dim=1)  # weighted sum over timesteps
        output = self.fc(context)  # final prediction
        return output