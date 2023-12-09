from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from database import environments_crud, provisioned_environments_crud, finetuned_models_crud, ssh_crud, fine_tunings_crud
from configs.modellibrary import MODELS as pretrained_models
from utils.auth_handler import auth_handler
from .schemas import *
from .utils import *

import requests
import configs.ansible
import configs.ansible.docs
import os

router = APIRouter(prefix='/experiments/inference', tags=['experiments - inference'])


@router.post("/provision")
def provision_environment_for_inference(data: ProvisionEnvironment, user: auth_handler.auth_wrapper = Depends()):
    # verify environment
    environment = environments_crud.get_by_id(data.environment_id)
    if not environment:
        raise HTTPException(404, detail="environment does not exist")
    
    # get hostname
    hostname = environment["hostname"]
    
    # verify model
    if data.model_is_pretrained:
        model = next(filter(lambda x: x["_id"] == data.model_id, pretrained_models), None)  
    else: 
        model = finetuned_models_crud.get_by_id(data.model_id)
        
    if not model:
        raise HTTPException(404, detail="model does not exist")
    
    # verify provision
    provisioning = provisioned_environments_crud.get({"name": data.name})
    if provisioning:
        raise HTTPException(404, detail="name is already in use")
    
    # verify provision name
    if " " in data.name.strip():
        raise HTTPException(400, detail="name should not include any spaces") 
    print("--- completed checks ---")
    
    # start server
    successful = setup_server(environment, name=data.name)
    if not successful:
        raise HTTPException(500, detail="an error occured while setting up the machine")
    
    # generate address
    print("--- started server ---")
    generated_url = f'http://{hostname}:{configs.INFERENCE_PORT}'
    print("--- generated url:", generated_url, "---")
    
    # test valid connection
    try:
        requests.get(generated_url)
    except Exception as e:
        raise HTTPException(500, detail="an error occurred while setting up")
    
# setup user on remote environment
    response = requests.post(f"{generated_url}/setup/user", json={"user_id": user["_id"]})
    response.raise_for_status()
    print("--- setup user on environment ---")
    
    # setup model on remote environment
    requests.post(f"{generated_url}/setup/model", json={
                                            "model_id": model["_id"],
                                            "category": model["category"],
                                            "is_pretrained": data.model_is_pretrained
                                        })
    print("--- setup model on environment ---")
    
    # save to db
    provisioned_environments_crud.create({
        "endpoint": generated_url,
        "user_id": user["_id"],
        "status": "active",
        **data.dict()
    })
    
    # update environment [is provisioned]
    environments_crud.update({"is_provisioned": True}, data.environment_id)
    return 1


# add model to provisioned endpoint
@router.patch("/provision/{_id}")
def update_models_on_environment(_id: str, data: AddProvisionEnvironmentModel, user: auth_handler.auth_wrapper = Depends()):
    # verify model
    model = next(filter(lambda x: x["_id"] == data.model_id, 
                        pretrained_models), None) if data.model_is_pretrained else fine_tunings_crud.get_by_id(data.model_id)
    if not model:
        raise HTTPException(404, detail="model does not exist")
    
    # verify provision
    provisioning = provisioned_environments_crud.get_by_id(_id)
    if not provisioning:
        raise HTTPException(404, detail="setup does not exist")
    
    # setup model on remote environment
    requests.post(f"{provisioning['endpoint']}/setup/model", json={
                                            "model_id": model["_id"],
                                            "category": model["category"],
                                            "is_pretrained": data.model_is_pretrained
                                        })
    print("--- setup model on environment ---")
    
    # update provision
    provisioned_environments_crud.update({
        "models": [*provisioning.get("models", [provisioning["model_id"]])]
    }, _id)
    return 1


# stop provisioned endpoint
@router.delete("/provision/{_id}")
def destroy_provisioned_endpoint(_id: str, _: auth_handler.auth_wrapper = Depends()):
    # verify provision
    provisioning = provisioned_environments_crud.get_by_id(_id)
    if provisioning:
        raise HTTPException(404, detail="server does not exist")
    
    # setting dynamic path
    uninstall_path = configs.ansible.ANS_UNINSTALL_PATH.replace("<name>", provisioning["name"])
    inventory_path = configs.ansible.INVENTORY_PATH.replace("<name>", provisioning["name"])
        
    # setup ansible container
    p = os.popen(f"ansible-playbook {uninstall_path} -i {inventory_path}")
    print(p.read())
    
    provisioned_environments_crud.update({"status": "stopped"}, _id)
    environments_crud.update({"is_provisioned": False}, provisioning["environment_id"])
    return 1


@router.get("/provision")
def get_provisioned_endpoints(user: auth_handler.auth_wrapper = Depends()):
    provisions = provisioned_environments_crud.get_all({"user_id": user["_id"]})
    
    # set dataset & model name
    for provision in provisions:
        if provision["model_is_pretrained"]:
            provision["model"] = next(filter(lambda x: x["_id"] == provision["model_id"], pretrained_models), None) 
        else: 
            provision["model"] = fine_tunings_crud.get_by_id(provision["model_id"])
            
        provision["environment"] = environments_crud.get_by_id(provision["environment_id"])
        
    return provisions
