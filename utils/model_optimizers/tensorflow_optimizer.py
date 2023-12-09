from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
from typing import Optional

from .openvino_setup import optimize_model

import tensorflow.compat.v1 as tf_v1
import tensorflow as tf
import shutil
import os

import configs


def convert_v2_keras_model_to_pb(input_model_path: str, output_path: str) -> str:
    """
    Convert a Keras model saved in the HDF5 format (`.h5`) to TensorFlow's SavedModel format (`.pb`).

    Args:
        input_model_path (str): The path to the input Keras model file in HDF5 format.
        output_path (str): The path where the converted SavedModel should be saved.

    Returns:
        str: The path to the converted SavedModel.
    """
    # Load the Keras model
    model = tf.keras.models.load_model(input_model_path)

    # Save the model in SavedModel format
    tf.saved_model.save(model, output_path)

    return output_path


def convert_v1_keras_model_to_pb(input_model_path: str, output_path: str) -> str:
    """
    Convert a Keras model saved in the HDF5 format (`.h5`) using TensorFlow v1 to TensorFlow's SavedModel format (`.pb`).

    Args:
        input_model_path (str): The path to the input Keras model file in HDF5 format.
        output_path (str): The path where the converted SavedModel should be saved.

    Returns:
        str: The path to the converted SavedModel.
    """
    # Load the Keras model using TensorFlow v1
    model = tf_v1.keras.models.load_model(input_model_path)

    # Save the model in SavedModel format using TensorFlow v1
    tf_v1.saved_model.save(model, output_path)

    return output_path


def freeze_tf_model(model_directory: str, frozen_model_dir: str = '.', frozen_model_path: str = 'frozen_model.pb') -> str:
    """
    Freeze a TensorFlow SavedModel and convert it into a frozen graph in the Protobuf format (`.pb`).

    Args:
        model_directory (str): The path to the directory containing the TensorFlow SavedModel.
        frozen_model_dir (str): The directory where the frozen model should be saved. Defaults to the current directory ('.').
        frozen_model_path (str): The filename of the frozen model. Defaults to 'frozen_model.pb'.

    Returns:
        str: The path to the frozen model.
    """
    # Load the SavedModel
    imported = tf.saved_model.load(model_directory)

    # Retrieve the concrete function and freeze it
    concrete_func = imported.signatures[tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY]
    frozen_func = convert_variables_to_constants_v2(concrete_func,
                                                    lower_control_flow=False,
                                                    aggressive_inlining=True)

    # Retrieve the GraphDef and save it in the Protobuf format
    graph_def = frozen_func.graph.as_graph_def(add_shapes=True)
    tf.io.write_graph(graph_def, frozen_model_dir,
                      frozen_model_path, as_text=False)

    # Return the path to the frozen model
    return os.path.join(frozen_model_dir, frozen_model_path)


def convert_tf_to_openvino(
    model_path: str,
    export_name: str,
    tf_version: int = 2,
    is_frozen: bool = False,
    device: Optional[str] = None
):
    """
    Convert a TensorFlow model to OpenVINO format for inference using the Intel Distribution of OpenVINO Toolkit.

    Args:
        model_path (str): Path to the input TensorFlow model (.pb or .h5).
        export_name (str): Path where the converted OpenVINO model should be saved.
        tf_version (int, optional): TensorFlow version of the model. Defaults to 2.
        is_frozen (bool, optional): Indicates if the input model is already frozen. Defaults to False.
        device (str, optional): The target device for model optimization. If None, the default device will be used.

    Raises:
        ValueError: If the model file format is invalid.

    Note:
        - If `is_frozen` is True, it is assumed that the input model is already frozen.
        - If `is_frozen` is False, the function checks if the model_path is a .h5 file and converts it to a frozen .pb model.
        - The function uses the `convert_v2_keras_model_to_pb` and `convert_v1_keras_model_to_pb` functions to convert .h5 models to .pb models.
        - The function uses the `freeze_tf_model` function to freeze the model and create a frozen .pb model.
        - The function uses the `optimize_model` function to optimize the model for the target device using the Intel Distribution of OpenVINO Toolkit.
    """
    
    # Generate exporting path
    tensorflow_folder = f'{configs.TEMP_FOLDER}/_optimized/tensorflow'
    os.makedirs(tensorflow_folder, exist_ok=True)
    export_path = f"{tensorflow_folder}/{export_name}"
    
    # If the model is already frozen, optimize it directly
    if is_frozen:
        optimize_model(model_path, export_path, device=device)
        return export_path
 
    # TODO: generate random values for the model name
    models_dir = '_main_model'
    frozen_model_dir = '_frozen_models'
    frozen_model_path = 'frozen_model.pb'
    
    # create the directory
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(frozen_model_dir, exist_ok=True)

    if os.path.isfile(model_path) and model_path.endswith('.h5'):
        # Convert Keras model to .pb format
        if tf_version == 2:
            model_path = convert_v2_keras_model_to_pb(model_path, models_dir)
        else:
            model_path = convert_v1_keras_model_to_pb(model_path, models_dir)

    # if the path isn't a directory, raise an error
    elif not os.path.isdir(model_path):
        raise ValueError("Invalid model file format. Please provide a valid .h5 file.")

    # Freeze the model
    frozen_model_path = freeze_tf_model(model_path, 
                                        frozen_model_dir=frozen_model_dir, 
                                        frozen_model_path=frozen_model_path)

    # Optimize the frozen model
    optimize_model(frozen_model_path, export_path, device=device)

    # Remove temporary directories
    shutil.rmtree(frozen_model_dir)
    if os.path.isdir(models_dir):
        shutil.rmtree(models_dir)
        
    return export_path
