import torch
import onnx
from onnxsim import simplify
import os

def export_model(model, device, input_size, output_path):
    """
    Exporta un modelo de PyTorch a formato ONNX y simplifica el modelo ONNX.

    :param model: Modelo de PyTorch que se quiere exportar.
    :param device: Dispositivo de PyTorch que se está usando para el entrenamiento
    :param input_size: Tamaño de entrada del modelo (ejemplo: (batch_size, channels, height, width)).
    :param output_path: Ruta donde se guardará el modelo ONNX.
    """
    # Establecer el modelo en modo de evaluación
    model.eval()

    # Crear un tensor de entrada ficticio
    dummy_input = torch.randn(*input_size).to(device)

    # Verificar y crear el directorio de exportación si no existe
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f'[*] Directorio creado: {output_dir}')

    # Exportar el modelo a formato ONNX
    torch.onnx.export(
        model, dummy_input, output_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,  # Optimización de constantes
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},  # Eje dinámico para el tamaño del lote
            'output': {0: 'batch_size'}
        }
    )

    # Cargar el modelo ONNX para simplificar
    model_onnx = onnx.load(output_path)

    # Simplificar el modelo ONNX
    model_simplified, check = simplify(model_onnx)

    # Guardar el modelo simplificado
    onnx.save(model_simplified, output_path)

    print(f'[*] Modelo exportado y simplificado a: {output_path}')