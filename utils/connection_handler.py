from pssh.clients import SSHClient
from fastapi import HTTPException

from db_crudbase.pyobjectid import PyObjectId
from database import ssh_crud

import base64
import uuid
import os


def connect_to_host_with_pkey(hostname, user, environment_id):
    """
    Function that will connect to a host using a private key.

    :param str hostname: The hostname of the machine.
    :param str user: The username for the machine.
    :param int environment_id: The ID of the environment record
    for this machine.
    """

    key_bytes = ssh_crud.get({"environment_id": PyObjectId(environment_id)}).get("key_file")
    if not key_bytes:
        raise HTTPException(status_code=404, detail="A key could not be found for this environment.")


    # Generating a unique ID for temporary disk-storage of SSH key
    file_id = uuid.uuid1()
    ssh_key_path = f"{file_id}.pem"

    # Writing ssh key to disk temporarily
    with open(ssh_key_path, "wb") as temp_file:
        private_data = base64.b64decode(key_bytes)
        temp_file.write(private_data)

    # Connecting to new platform via SSH
    try:
        ssh_client = SSHClient(host=hostname, pkey=ssh_key_path, user=user)
    except Exception as e:
        return None

    # Removing ssh key file after connection is established
    os.remove(ssh_key_path)
    return ssh_client


def connect_to_host_with_password(hostname, user, environment_id):
    """
    Function that will connect to a host using a password.

    :param str hostname: The hostname of the machine.
    :param str user: The username for the machine.
    :param int environment_id: The ID of the environment record
    for this machine.
    """

    password = ssh_crud.get({"environment_id": PyObjectId(environment_id)}).get("password")
    if not password:
        raise HTTPException(status_code=404, detail="Password for this environment could not be found.")

    # Connecting to new platform via SSH
    try:
        ssh_client = SSHClient(host=hostname, password=password, user=user)
    except Exception as e:
        return None
    
    return ssh_client
