import os
import configs

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from datetime import datetime

from utils.model_optimizers import tensorflow_optimizer, pytorch_optimizer, onnx_optimizer
from utils.blobs_handler import upload_file_to_azure
from utils.auth_handler import auth_handler
from database import uploaded_models_crud

from . import utils as models_utils

router = APIRouter(prefix='/models', tags=['models - uploaded'])


@router.get('')
def get_models(user: auth_handler.auth_wrapper = Depends()):
    models = uploaded_models_crud.get_all({"user_id": user["_id"]})
    return models


@router.get('/{model_id}')
def get_model_details(model_id: str, user: auth_handler.auth_wrapper = Depends()):
    model = uploaded_models_crud.get_by_id(model_id)
    return model


@router.post('')
async def create_model(framework: str = Form(), tf_version: int = Form(1), model_file: UploadFile = File(), 
                        category: str = Form(), is_frozen: bool = Form(False), pytorch_model_class: UploadFile = File(None), 
                        model_name: str = Form(), user: auth_handler.auth_wrapper = Depends()):
    # validate framework
    allowed_frameworks = ["tensorflow", "pytorch", "onnx"]
    if framework not in allowed_frameworks:
        raise HTTPException(400, detail="framework is not valid")
    
    # validate category
    if category not in configs.MODEL_CATEGORIES:
        raise HTTPException(400, detail="category is not valid")
    
    # update model name
    model_name = model_name.replace(" ", "_")
    
    # save model file
    model_file_path = await models_utils.save_model_file(model_file=model_file, user_id=user["_id"])
    model_path_name = f'{user["_id"]}_{model_name}'
    
    # handle tensorflow optimization
    if framework == 'tensorflow':
        optimized_models_path = tensorflow_optimizer.convert_tf_to_openvino(model_file_path, model_path_name, 
                                                                            tf_version, is_frozen)
        
    # handle pytorch optimization
    elif framework == 'pytorch':
        model_class_path = await models_utils.save_model_file(model_file=pytorch_model_class, user_id=user["_id"])
        
        # convert pytorch model to onnx
        onnx_model_path = models_utils.get_onnx_model_path(user_id=user["_id"])
        optimized_models_path = pytorch_optimizer.convert_pytorch_to_openvino(model_class_path, model_file_path, model_path_name, onnx_model_path=onnx_model_path)
        
    # handle onnx opimization
    else:
        optimized_models_path = onnx_optimizer.convert_onnx_to_openvino(model_file_path, model_path_name)
    
    # handle name update
    xml_model = optimized_models_path + '.xml'
    bin_model = optimized_models_path + '.bin'
    
    # save models data to azure blob
    folder = f'{user["_id"]}/{model_name}'
    xml_model_url = upload_file_to_azure(open(xml_model, 'rb'), folder=folder)
    bin_model_url = upload_file_to_azure(open(bin_model, 'rb'), folder=folder)
    model_file_url = upload_file_to_azure(open(model_file_path, 'rb'), folder=folder)
    model_class_url = '' if framework != 'pytorch' else upload_file_to_azure(open(model_class_path, 'rb'), folder=folder)
    
    # add to db
    uploaded_models_crud.create({        
        "files": {
            "xml": xml_model_url,
            "bin": bin_model_url,
            "model": model_file_url,
            "model_class": model_class_url,
        },
        
        "name": model_name,
        "category": category,
        "framework": framework,
        
        "user_id": user["_id"],
        "created_on": datetime.now().strftime('%m-%d-%Y %H:%M:%S'),
        "size": round(os.path.getsize(model_file_path) / (1024 * 1024), 2),
        
    })
    
    # delete files
    os.remove(model_file_path)
    os.remove(xml_model)
    os.remove(bin_model)

    return 1


@router.delete('/{model_id}')
def delete_model(model_id: str, user: auth_handler.auth_wrapper = Depends()):
    model = uploaded_models_crud.get({"_id": model_id, "user_id": user["_id"]})
    if model is None:
        raise HTTPException(404, detail='model not found')

    uploaded_models_crud.delete(model_id)
    return model_id
