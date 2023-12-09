from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from database import fine_tunings_crud, datasets_crud, experiments_crud, environments_crud, finetuned_models_crud
from routes import utils as route_utils

from utils.experiments_handler.fine_tune import run_fine_tuning_experiment
from configs.modellibrary import MODELS as pretrained_models
from utils.auth_handler import auth_handler
from .schemas import *

import configs


router = APIRouter(prefix='/experiments/fine-tune', tags=['experiments - fine-tune'])


@router.get("")
def get_fine_tune_experiments(recent: Optional[bool] = False, user: auth_handler.auth_wrapper = Depends()):
    fine_tunings = sorted(fine_tunings_crud.get_all({"user_id": user["_id"]}), 
                        key=lambda x: x["created_on"], reverse=True)
    if recent:  # handle recent query
        fine_tunings = fine_tunings[:5]

    # set dataset & model name
    for fine_tuning in fine_tunings:
        fine_tuning["dataset"] = datasets_crud.get_by_id(fine_tuning["dataset_id"])
        fine_tuning["environment"] = environments_crud.get_by_id(fine_tuning["environment_id"])
        fine_tuning["model"] = next(filter(lambda x: x["_id"] == fine_tuning["model_id"], pretrained_models), None)
        
    return fine_tunings


@router.get("/{fine_tuning_id}")
def get_fine_tuning_item(fine_tuning_id: str, user: auth_handler.auth_wrapper = Depends()):
    fine_tuning = fine_tunings_crud.get({"user_id": user["_id"], "_id": fine_tuning_id})
    fine_tuning["dataset"] = datasets_crud.get_by_id(fine_tuning["dataset_id"])  
    fine_tuning["environment"] = environments_crud.get_by_id(fine_tuning["environment_id"])
    fine_tuning["model"] = next(filter(lambda x: x["_id"] == fine_tuning["model_id"], pretrained_models), None)

    return fine_tuning


@router.post("") 
def create_fine_tuning_experiment(data: CreateFinetuneExperiment, user: auth_handler.auth_wrapper = Depends()):
    # verify fine_tune doesn't exist
    existing_fine_tune = fine_tunings_crud.get({"user_id": user["_id"], "name": data.name})
    if existing_fine_tune is not None:
        raise HTTPException(403, detail="fine-tune experiment already exists")

    # verify user has project permissions
    project = route_utils.verify_project_exists(data.project_id)
    has_permissions = route_utils.verify_user_project_permissions(user["_id"], project)

    if not has_permissions:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    # set extra details
    data = data.dict()
    data["status"] = "new"
    data["user_id"] = user["_id"]
    data["created_on"] = datetime.now().timestamp()

    # create environment
    fine_tunings_crud.create(data)
    return 1


@router.get('/{fine_tuning_id}/experiments')
def get_fine_tuning_experiments(fine_tuning_id: str, user: auth_handler.auth_wrapper = Depends()):

    # verify fine_tuning exists
    fine_tuning = fine_tunings_crud.get({"user_id": user["_id"], "_id": fine_tuning_id})
    if fine_tuning is None:
        raise HTTPException(403, detail="fine-tune experiment does not exists")
    
    experiments = experiments_crud.get_all({"type": "fine_tuning", "experiment_id": fine_tuning_id})
    return sorted(experiments, key=lambda x: x["created_on"], reverse=True)


@router.post('/{fine_tuning_id}/experiment')
def run_fine_tuning_experiments(data: CreateFinetuneRun, fine_tuning_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get fine_tuning
    fine_tuning = fine_tunings_crud.get({"_id": fine_tuning_id, "user_id": user["_id"]})
    if fine_tuning is None:
        raise HTTPException(403, detail="This fine-tune experiment doesn't exist")
    
    # verify model, env, etc.
    pretrained_model = next(filter(lambda x: x["_id"] == fine_tuning["model_id"], pretrained_models), None)
    if pretrained_model is None:
        raise HTTPException(404, detail="model does not exist")
     
    environment = environments_crud.get({"_id": fine_tuning["environment_id"], "user_id": user["_id"]})
    if environment is None:
        raise HTTPException(403, detail="This environment doesn't exist")
    
    # update fine_tuning
    fine_tunings_crud.update({"status": "pending"}, fine_tuning_id)
    
    # set time last used to environment
    environments_crud.update({"last_used": datetime.now().timestamp()}, fine_tuning["environment_id"])
    
    # run fine_tuninging experiment
    response_data = run_fine_tuning_experiment(environment_data=environment, 
                                    fine_tune_data=fine_tuning, **data.dict())

    # save experiment run
    experiments_crud.create({
        "created_on": datetime.now().timestamp(),
        "experiment_id": fine_tuning["_id"],
        "user_id": user["_id"],
        "type": "fine_tune",
        **response_data
    })

    # Updating experiment result status 
    if response_data["is_successful"]:
        fine_tunings_crud.update({"status": "executed"}, fine_tuning["_id"])
    else:
        fine_tunings_crud.update({"status": "failed"}, fine_tuning["_id"])
        return response_data
    
    # create new finetuned model if response was successful
    finetuned_models_crud.create({
        "files": {
            "model": response_data["response"]["data"],
            "base": fine_tuning["model_id"]
        },
        
        "user_id": user["_id"],
        "name": fine_tuning["name"],
        "category": pretrained_model["category"],
        "created_on": datetime.now().timestamp(),
    })
    return response_data


@router.delete('/{fine_tuning_id}')
def delete_fine_tuning(fine_tuning_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get fine_tuning
    fine_tuning = fine_tunings_crud.get({"_id": fine_tuning_id, "user_id": user["_id"]})
    if fine_tuning is None:
        raise HTTPException(403, detail="This fine-tune experiment doesn't exist")
    
    fine_tunings_crud.delete(fine_tuning_id)
    return 1
