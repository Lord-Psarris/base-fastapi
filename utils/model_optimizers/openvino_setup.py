from openvino.runtime import Core, serialize

import os


def optimize_model(model_path: str, export_path: str, device: str = None):
    """
    Optimizes a model by converting it to the OpenVINO Intermediate Representation (IR) format.

    Args:
        model_path (str): Path to the input model file.
        export_path (str): Path to export the optimized model in IR format.
        device (str, optional): The target device for optimization. Defaults to None.

    Raises:
        FileNotFoundError: If the input model file does not exist.
        ValueError: If the specified device is not available for inference.

    Returns:
        None

    Example:
        optimize_model("model.pb", "optimized_model", device="CPU")

    """
    ie = Core()

    # Check if the input model file exists
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Input model file not found: {model_path}")

    # Get available inference devices
    devices = ie.available_devices

    # Check if the specified device is available for inference
    if device and device not in devices:
        raise ValueError(f"Specified device '{device}' is not available for inference. Available devices: {devices}")

    # Set the target device for optimization
    device = devices[0] if not device else device

    # Read the input model using the Inference Engine
    model_tf = ie.read_model(model=model_path)

    # Serialize the optimized model in IR format
    serialize(model_tf, xml_path=f"{export_path}.xml")

