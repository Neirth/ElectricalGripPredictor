from models.electrical_grid import GridLinearModel

import time
import torch
import torch.nn as nn
import torch.optim as optim

def r2_score_torch(y_true, y_pred):
    """
    Calcula R^2 utilizando PyTorch.

    :param y_true: Tensor de valores reales.
    :param y_pred: Tensor de valores predichos.
    :return: Valor de R^2.
    """
    # Calcular la media de los valores reales
    y_true_mean = torch.mean(y_true)

    # Calcular la suma de los cuadrados residuales y la suma total de cuadrados
    ss_res = torch.sum((y_true - y_pred) ** 2)  # Residual sum of squares
    ss_tot = torch.sum((y_true - y_true_mean) ** 2)  # Total sum of squares

    # Calcular R^2
    r2 = 1 - (ss_res / ss_tot)
    return r2.item()  # Devolver como un valor escalar

def train_model(train_loader, device, writer, epochs=300, learning_rate=0.001):
    """
    Entrena el modelo de predicción del siguiente valor en la red eléctrica usando ventanas deslizantes.

    :param train_loader: DataLoader para el conjunto de entrenamiento.
    :param device: Dispositivo (CPU o GPU) para entrenar el modelo.
    :param writer: Escritor de TensorBoard para registrar la pérdida.
    :param epochs: Número de épocas para el entrenamiento.
    :param learning_rate: Tasa de aprendizaje para el optimizador.
    :return: El modelo entrenado.
    """
    # Crear un modelo
    model = GridLinearModel()
    model.to(device)  # Mover el modelo al dispositivo

    # Definir la función de pérdida y el optimizador
    criterion = nn.MSELoss()  # Usamos MSELoss para regresión
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    start_time = time.time()  # Medir el tiempo de entrenamiento

    # Entrenamiento
    for epoch in range(epochs):
        epoch_loss = 0.0  # Para almacenar la pérdida acumulada en cada época
        all_outputs = []
        all_targets = []

        for i, element in enumerate(train_loader):
            # Desempaquetamos los datos
            x = element['window_stack'].to(device)
            y = element['next_value'].to(device)

            # Forward pass
            outputs = model(x)

            # Asegurarse de que outputs y y tengan la misma forma
            outputs = torch.squeeze(outputs)

            # Calcular la pérdida
            loss = criterion(outputs, y)

            # Backward pass y optimización
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

            # Guardar los valores predichos y los reales para calcular el R²
            all_outputs.append(outputs.detach())
            all_targets.append(y.detach())

        # Concatenar las listas para obtener tensores
        all_outputs = torch.cat(all_outputs)
        all_targets = torch.cat(all_targets)

        # Promedio de pérdida por época
        avg_loss = epoch_loss / len(train_loader)

        # Calcular R² usando la función definida
        r2 = r2_score_torch(all_targets, all_outputs)

        # Exportar la pérdida y el R² a TensorBoard
        writer.add_scalar('Loss/train', avg_loss, epoch)
        writer.add_scalar('R2/train', r2, epoch)

        # Loggear cada época con pérdida y R²
        print(f'[#] Epoch [{epoch + 1}/{epochs}] -> Loss: {avg_loss:.4f}; R²: {r2:.4f}')

    total_time = time.time() - start_time
    print(f'[*] Entrenamiento completado en {total_time:.2f} segundos.')

    # Cerrar el SummaryWriter
    writer.close()

    return model