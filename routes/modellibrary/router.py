from fastapi import APIRouter, Depends

from utils.auth_handler import auth_handler
from database import finetuned_models_crud
from configs.modellibrary import MODELS

router = APIRouter(prefix='/models/library', tags=['models - library'])
# TODO: setup route to provision model on env


@router.get('')
def get_library_models(_: auth_handler.auth_wrapper = Depends()):
    return MODELS


@router.get('/fine-tuned')
def get_fine_tuned_models(user: auth_handler.auth_wrapper = Depends()):
    return finetuned_models_crud.get_all({"user_id": user["_id"]})
