from .openvino_setup import optimize_model

import configs

import importlib.util
import torch
import os


def get_model_class(file_path: str):
    """
    Load a Python file as a module and retrieve the model class defined within.
    Note: the model class must be defined in the `model` variable

    Args:
        file_path (str): Path to the Python file containing the model class.

    Raises:
        FileNotFoundError: If the specified Python file does not exist.
        AttributeError: If the model class is not found in the module.

    Returns:
        type: The model class defined in the Python file.

    Example:
        model_class = get_model_class("model.py")
        model = model_class()
    """
    # Load the Python file as a module
    module_name = os.path.splitext(file_path)[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Read the `model` variable from the module
    if not hasattr(module, "model"):
        raise AttributeError('Model class not found in the specified module')

    model_class = module.model
    return model_class



def get_pytorch_model(model_class_path: str, model_file_path: str) -> torch.nn.Module:
    """
    Load a PyTorch model from a file using the provided model class.

    Args:
        model_class_path (str): Path to the Python file containing the model class.
        model_file_path (str): Path to the file containing the PyTorch model's weights.

    Returns:
        torch.nn.Module: The loaded PyTorch model.

    Example:
        model = get_pytorch_model("model.py", "model.pth")
        model.eval()
    """
    # Get model class
    model = get_model_class(model_class_path)
    
    # Load model
    model.load_state_dict(torch.load(model_file_path))
    model.eval()
    
    return model


def convert_pytorch_to_onnx(model_class_path: str, model_file_path: str, onnx_model_path: str) -> str:
    """
    Convert a PyTorch model to ONNX format and save it to the specified file path.

    Args:
        model_class_path (str): Path to the Python file containing the model class.
        model_file_path (str): Path to the file containing the PyTorch model's weights.
        onnx_model_path (str): Path to save the converted ONNX model.

    Returns:
        str: The path to the saved ONNX model.

    Example:
        onnx_model_path = convert_pytorch_to_onnx("model.py", "model.pth", "model.onnx")
    """
    # Get PyTorch model
    model = get_pytorch_model(model_class_path, model_file_path)
    
    # Prepare example input tensor
    example_input = torch.randn(1, 3, 224, 224)  # TODO: Adjust the shape and data type as per your model's input requirements

    # Convert the model to ONNX format
    torch.onnx.export(model, example_input, onnx_model_path, export_params=True, opset_version=11)
    return onnx_model_path



def convert_pytorch_to_openvino(model_class_path: str, model_file_path: str, export_name: str, onnx_model_path: str = None):
    """
    Convert a PyTorch model to OpenVINO format and save the optimized model.

    Args:
        model_class_path (str): Path to the Python file containing the model class.
        model_file_path (str): Path to the file containing the PyTorch model's weights.
        export_name (str): Name for the exported OpenVINO model.

    Returns:
        str: The path to the saved optimized OpenVINO model.

    Example:
        export_path = convert_pytorch_to_openvino("model.py", "model.pth", "optimized_model")
    """
    # Generate a random name for the ONNX model
    onnx_model = 'onnx_model.onnx' if onnx_model_path is None else onnx_model_path
    
    # Generate exporting path
    pytorch_folder = f'{configs.TEMP_FOLDER}/_optimized/pytorch'
    os.makedirs(pytorch_folder, exist_ok=True)
    export_path = f"{pytorch_folder}/{export_name}"
    
    # Optimize PyTorch model
    onnx_model = convert_pytorch_to_onnx(model_class_path=model_class_path, model_file_path=model_file_path, onnx_model_path=onnx_model)
    optimize_model(model_path=onnx_model, export_path=export_path)

    # Clean up
    os.remove(onnx_model)
    
    return export_path
