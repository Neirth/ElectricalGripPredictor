import torch
from sklearn.metrics import r2_score

def evaluate_model(model, val_loader, device, writer, epoch=200):
    """
    Evalúa la precisión del modelo en un conjunto de datos con ventanas deslizantes.

    :param model: Modelo de PyTorch a evaluar.
    :param val_loader: DataLoader que contiene los datos para la evaluación.
    :param device: Dispositivo donde se ejecuta el modelo (CPU o GPU).
    :param writer: Escritor de TensorBoard para registrar la precisión.
    :param epoch: Número de la época actual, usado para el registro en TensorBoard.
    """
    model.eval()  # Poner el modelo en modo de evaluación
    y_true = []
    y_pred = []

    with torch.no_grad():  # No calcular gradientes para la evaluación
        for i, element in enumerate(val_loader):
            # Desempaquetamos los datos
            x = element['window_stack']
            y = element['next_value']

            # Hacer predicciones
            outputs = model(x)  # Asegúrate de que tu modelo acepte timestamps

            # Supongamos que el modelo devuelve un valor continuo
            predicted = outputs.squeeze()  # Eliminar dimensiones innecesarias

            # Almacenar las predicciones y los valores verdaderos
            y_true.extend(y.cpu().numpy())  # Asegúrate de que sean tensores de CPU
            y_pred.extend(predicted.cpu().numpy())

    # Calcular R^2
    r2 = r2_score(y_true, y_pred)  # Usar la función r2_score de sklearn
    print(f'[*] R^2 del modelo en el conjunto de evaluación: {r2:.4f}')

    # Registrar R^2 en TensorBoard
    writer.add_scalar('R2', r2, epoch)