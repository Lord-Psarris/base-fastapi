from fastapi import File
from typing import Union
from uuid import uuid4

import os

import configs


async def save_model_file(model_file: File, user_id: Union[int, str]) -> str:
    temp_folder = configs.TEMP_FOLDER
    temp_model_path = f"{temp_folder}/{user_id}"
    
    # create folder and define path
    os.makedirs(temp_model_path, exist_ok=True)
    model_path = os.path.join(temp_model_path, model_file.filename)
    
    with open(model_path, "wb") as file:
        file_data = await model_file.read()
        file.write(file_data)
        
    return model_path


def get_onnx_model_path(user_id: Union[int, str]) -> str:
    temp_folder = configs.TEMP_FOLDER
    temp_model_path = f"{temp_folder}/{user_id}"
    
    # create folder and define path
    os.makedirs(temp_model_path, exist_ok=True)
    model_path = os.path.join(temp_model_path, f"{uuid4()}.onnx")
    
    return model_path
