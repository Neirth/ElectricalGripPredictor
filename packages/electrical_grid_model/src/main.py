from utils.trainer import train_model
from utils.export import export_model
from utils.evaluation import evaluate_model

from datasets.electrical_grid import ElectricalGridDataset
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

import os
import torch

BATCH_SIZE=64
DATA_FILE = os.path.join(os.getcwd(),  './assets/LD2011_2014.csv')

def main():
    # Avisamos de la intención de este modulo
    print(f'[*] Modulo de entrenamiento para el modelo "Electrical_Grid"')

    # We try to use the best device as possible
    device = torch.device("mps")

    print(f'[*] El dispositivo a usar será "{device}"')

    # Prepare dataset
    dataset = ElectricalGridDataset(DATA_FILE, device)
    train_dataset, val_dataset = train_test_split(dataset, test_size=0.2, random_state=42)

    # Load into PyTorch the dataset
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)  # No es necesario barajar en validación

    # Preparamos la captura de datos en el tensorboard
    writer = SummaryWriter(log_dir="./runs")

    # Train and Test Model
    model = train_model(train_loader, device, writer)
    evaluate_model(model, val_loader, device, writer)

    # Export Model
    export_model(
        model,
        device,
        input_size = (1, 19, 3),
        output_path = './build/grid_predictor.onnx'
    )

    # Cerramos el reporte de entrenamiento
    writer.close()

if __name__ == "__main__":
    main()