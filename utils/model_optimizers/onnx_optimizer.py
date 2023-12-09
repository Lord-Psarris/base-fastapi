from .openvino_setup import optimize_model

import configs
import os

def convert_onnx_to_openvino(onnx_model_path: str, export_name: str) -> str:
    """
    Convert an ONNX model to OpenVINO format for inference using the Intel Distribution of OpenVINO Toolkit.

    Args:
        onnx_model_path (str): Path to the input ONNX model.
        export_name (str): Name for the exported OpenVINO model.

    Returns:
        str: Path to the converted OpenVINO model.

    Note:
        - The function creates a directory "_optimized/onnx" to store the exported OpenVINO model.
        - The function uses the `optimize_model` function to optimize the ONNX model for the target device using the Intel Distribution of OpenVINO Toolkit.
    """
    # Generate the exporting path
    onnx_folder = f'{configs.TEMP_FOLDER}/_optimized/onnx'
    os.makedirs(onnx_folder, exist_ok=True)
    export_path = f"{onnx_folder}/{export_name}"

    # Optimize the ONNX model
    optimize_model(model_path=onnx_model_path, export_path=export_path)

    return export_path