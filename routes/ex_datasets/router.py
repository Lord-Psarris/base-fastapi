from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from utils.auth_handler import auth_handler
from routes import utils as route_utils
from database import datasets_crud
from .schemas import *


router = APIRouter(prefix='/experiments/datasets', tags=['experiments - fine-tune - datasets'])


@router.get("")
def get_datasets(user: auth_handler.auth_wrapper = Depends()):
    datasets = sorted(datasets_crud.get_all({"user_id": user["_id"]}), 
                        key=lambda x: x["created_on"], reverse=True)
    return datasets


@router.post("/image-classification")
def upload_image_classification_dataset(data: CreateICDataset, user: auth_handler.auth_wrapper = Depends()):
    """
    Note: the annotations file should be in the coco dataset format (https://cocodataset.org/#format-data):-
    ```
    {
        ...,
        "images": [
            {
                "id": 1,
                "width": 240,
                "height": 240,
                "file_name": "image1.jpg",
                ...
            }
        ],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                ...
            }
        ],
        "categories": [
            {
                "id": 1,
                "name": "cat",
                "supercategory": "animal" // Optional
            }
        ]
    }
    ```
    """
    # verify the complete dataset is uploaded
    if not data.images or not data.annotations:
        raise HTTPException(400, detail="please upload the complete dataset requirements")
    
    # verify dataset does not exist
    if datasets_crud.get({"name": data.name, "user_id": user["_id"]}):
        raise HTTPException(400, detail="dataset already exists")
        
    # create dataset
    datasets_crud.create({
        "user_id": user["_id"],
        "use_from_library": False,
        "type": "image-classification",
        "created_on": datetime.now().timestamp(),
        **data.dict()
    })
    
    return 1


@router.post("/llama")
def upload_llama_dataset(data: CreateLlamaDataset, user: auth_handler.auth_wrapper = Depends()):
    # TODO: allow access to private libraries from huggingface
    
    # verify dataset does not exist
    if datasets_crud.get({"name": data.name, "user_id": user["_id"]}):
        raise HTTPException(400, detail="dataset already exists")
    
    # create dataset
    datasets_crud.create({
        "user_id": user["_id"],
        "use_from_library": True,
        "type": "generative-text",
        "created_on": datetime.now().timestamp(),
        **data.dict()
    })
    
    return 1
    


@router.delete('/{dataset_id}')
def delete_dataset(dataset_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get dataset
    dataset = datasets_crud.get({"_id": dataset_id, "user_id": user["_id"]})
    if dataset is None:
        raise HTTPException(403, detail="This dataset doesn't exist")
    
    datasets_crud.delete(dataset_id)
    return 1
