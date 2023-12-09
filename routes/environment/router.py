from fastapi import APIRouter, Depends , Request, UploadFile, File, Form, HTTPException

from utils.host_handler import connect_to_remote_host, connect_to_remote_host_password
from database import environments_crud, ssh_crud
from utils.auth_handler import auth_handler
from . import utils as env_utils

import base64
import os

router = APIRouter(prefix='/environments', tags=['environments'])


@router.get('/')
def get_envrionments(user: auth_handler.auth_wrapper = Depends()):
    environments = environments_crud.get_all({"user_id": user["_id"]})
    return environments



@router.post('/vpn')
async def create_environemt_with_vpn(vpn: str = Form(None), port: str = Form(None), user: str = Form(None),
                        openvpn_client_cert: UploadFile = File(None), openvpn_client_conf: UploadFile = File(None), 
                        openvpn_client_key: UploadFile = File(None), openvpn_ca_cert: UploadFile = File(None)):
    return 1


@router.post('/')
async def create_environemt(request: Request, password: str = Form(None), hostname: str = Form(), ssh_key: UploadFile = File(None), 
                            username: str = Form(), name: str = Form(), user: auth_handler.auth_wrapper = Depends()):
    """
    Currently supports Unix-based environments Ubuntu and CentOS.
    """
    # verify environment isnt already added
    if environments_crud.get({"name": name, "user_id": user["_id"]}):
        raise HTTPException(status_code=400, detail="Environment already exists")

    # perform initial connection
    if ssh_key:
        ssh_client, os_name, ssh_key_path, error = await connect_to_remote_host(ssh_key=ssh_key, hostname=hostname, user=username)
    else:
        ssh_key_path = None
        ssh_client, os_name, error = await connect_to_remote_host_password(password=password, user=username, hostname=hostname)

    # handler generated error
    if error:
        raise HTTPException(status_code=error["status_code"], detail=error["detail"]) 

    # handle no password
    if ssh_key is None or ssh_key_path is None and not password:
        raise HTTPException(status_code=400, detail="Requires a private key or password.")

    # parse request data
    request_data = await request.form()
    request_data = dict(request_data)

    # update request data
    request_data["user_id"] = user["_id"]
    request_data["use_pkey"] = ssh_key != None # Do we have a private key?

    print("--- setting up environment ---")
    environment_data = env_utils.setup_environment(ssh_client, request_data, ssh_key, os_name)
    environment_data["is_provisioned"] = False
    environment = environments_crud.create(environment_data)

    # get ssh key from db
    if ssh_key and ssh_key_path:
        # Storing user's SSH key into MongoDB with environment id
        with open(ssh_key_path) as key_output:
            key_file = key_output.read()
            bytes = base64.b64encode(key_file.encode())
            
        # Deleting filepath once finished
        os.remove(ssh_key_path)
        ssh_crud.create({"key_file": bytes, "environment_id": environment["_id"]})
    
    return 1 
