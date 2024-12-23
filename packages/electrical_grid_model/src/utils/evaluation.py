import torch
from preprocessors.electrical_grid import calculate_r2_from_csv
from sklearn.metrics import r2_score

def evaluate_model(model, val_loader, device, writer, epoch=50):
    """
    Evaluates the accuracy of the model on a dataset with sliding windows.

    :param model: PyTorch model to evaluate.
    :param val_loader: DataLoader containing the data for evaluation.
    :param device: Device where the model runs (CPU or GPU).
    :param writer: TensorBoard writer to log the accuracy.
    :param epoch: Current epoch number, used for logging in TensorBoard.
    """
    model.eval()  # Set the model to evaluation mode
    y_true = []
    y_pred = []

    with torch.no_grad():  # Do not compute gradients for evaluation
        for i, element in enumerate(val_loader):
            # Unpack the data
            x = element['window_stack']
            y = element['next_value']

            # Make predictions
            outputs = model(x)  # Make sure your model accepts timestamps

            # Assume the model returns a continuous value
            predicted = outputs.squeeze()  # Remove unnecessary dimensions

            # Store the predictions and true values
            y_true.extend(y.cpu().numpy())  # Ensure these are CPU tensors
            y_pred.extend(predicted.cpu().numpy())

    # Calculate R^2
    r2_model = r2_score(y_true, y_pred)  # Use the r2_score function from sklearn
    print(f'[*] R^2 of the model on the evaluation set: {r2_model:.4f}')

    r2_prod = calculate_r2_from_csv('./assets/AUSTRIA_2015_2021.csv')
    print(f'[*] R^2 of the production forecast: {r2_prod:.4f}')

    # Log R^2 in TensorBoard
    writer.add_scalar('R2/eval', r2_model, epoch)