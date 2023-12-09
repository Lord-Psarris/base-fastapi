from .container_handler import start_benchmark_server, stop_benchmark_server, start_inference_server, stop_inference_server
from pssh.exceptions import AuthenticationError, UnknownHostException
from fastapi.exceptions import HTTPException
from pssh.clients import SSHClient
from fastapi import UploadFile

import configs
import uuid
import time
import os


async def connect_to_remote_host(ssh_key: UploadFile, hostname: str, user: str):
    """
    Connects to a remote host using a temporarily disk-written SSH key.

    :param str ssh_key: The private key to connect to the remote host.
    :param str hostname: The hostname of the remote host.
    :param str user: The username to connect to the remote host.
    """
    # Initializing variables for proper error handling
    ssh_client = None
    os_name = None

    # Generating a unique ID for temporary disk-storage of SSH key
    file_id = uuid.uuid1()
    ssh_key_path = f"{configs.TEMP_FOLDER}/{file_id}.pem"

    # Writing ssh key to disk temporarily
    private_key = await ssh_key.read()
    with open(ssh_key_path, "wb") as temp_file:
        temp_file.write(private_key)

    error = None
    # Connecting to new platform via SSH
    try:
        ssh_client = SSHClient(host=hostname, pkey=ssh_key_path, user=user)

    except AuthenticationError as e:
        os.remove(ssh_key_path)
        error = {"status_code": 400, "detail": "There was an error authenticating with the host. Please check credentials and try again."}
        return ssh_client, os_name, ssh_key_path, error

    except UnknownHostException as e:
        os.remove(ssh_key_path)
        error = {"status_code": 400, "detail": "The provided host does not appear to exist or is not accessible."}
        return ssh_client, os_name, ssh_key_path, error

    except Exception as e:
        print(e)
        os.remove(ssh_key_path)
        error = {"status_code": 500, "detail": "There was an error connecting with the host."}
        return ssh_client, os_name, ssh_key_path, error

    # Running commands in remote host to retrieve OS information
    host_info = ssh_client.run_command("egrep '^(VERSION|NAME)=' /etc/os-release ")
    for line in host_info.stdout:
        if "NAME" in line:
            os_name = line.split("=")[1].strip('"')

    return ssh_client, os_name, ssh_key_path, error


def perms_string(os_name: str, user: str):
    if os_name == "Ubuntu":
        return f'{user} ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/sbin/ufw, /usr/bin/docker, /usr/bin/firewall-cmd'
    if os_name == "CentOS Linux":
        return f'{user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/yum, /usr/bin/docker, /usr/bin/firewall-cmd'


def handle_passwordless_sudo(ssh_client: SSHClient, password: str, user: str, os_name: str):
    """
    Checks and sets up passwordless sudo commands for passworded connections. Not generally required
    for connections made with private keys.

    :param SSHClient client: The SSH client instance to use.
    """
    contains_entry = False
    sudoer_entries = ssh_client.run_command('sudo cat /etc/sudoers')
    sudoer_entries.stdin.write(f'{password}\n')
    sudoer_entries.stdin.flush()

    perms_str = perms_string(os_name=os_name, user=user)

    for line in sudoer_entries.stderr:
        print("Error: ", line)

    for line in sudoer_entries.stdout:
        if perms_str in line:
            contains_entry = True

    if contains_entry:
        return

    editing_perms = ssh_client.run_command(f"echo '\n# Measure Flapmax entry\n{perms_str}' | (sudo EDITOR='tee -a' visudo)", use_pty=True)
    editing_perms.stdin.write(f'{password}\n')
    editing_perms.stdin.flush()
    for line in editing_perms.stderr:
        print("Error edit: ", line)
        raise HTTPException(status_code=500, detail="Sudoer entry failed.")


async def connect_to_remote_host_password(password: str, hostname: str, user: str):
    """
    Connects to a remote host using a provided password
    and adds passwordless sudo permissions for the user.

    :param str password: The password to connect to the remote host.
    :param str hostname: The hostname of the remote host.
    :param str user: The username to connect to the remote host.
    """
    # Initializing variables for proper error handling
    ssh_client = None
    os_name = None
    error = None
    # Connecting to new platform via SSH
    try:
        ssh_client = SSHClient(host=hostname, password=password, user=user, timeout=5)

    except AuthenticationError as e:
        error = {"status_code": 400, "detail": "There was an error authenticating with the host. Please check credentials and try again."}
        return ssh_client, os_name, error

    except UnknownHostException as e:
        error = {"status_code": 400, "detail": "The provided host does not appear to exist or is not accessible."}
        return ssh_client, os_name, error

    except Exception as e:
        print(e)
        error = {"status_code": 500, "detail": "There was an error connecting with the host."}
        return ssh_client, os_name, error

    # Running commands in remote host to retrieve OS information
    host_info = ssh_client.run_command("egrep '^(VERSION|NAME)=' /etc/os-release ")
    for line in host_info.stdout:
        if "NAME" in line:
            os_name = line.split("=")[1].strip('"')

    handle_passwordless_sudo(ssh_client=ssh_client, password=password, user=user, os_name=os_name)
    
    return ssh_client, os_name, error


def download_fmax_docker_image(ssh_client, image_type: str = "benchmark"):
    """
    Downloads the fmax-docker image from Azure container registires and runs/stops it on a machine.
    
    :params image_type: this specifies the type of image to be pulled from the registry. [benchmark, inference]
    """
    success = False
    image_types = {
        "benchmark": {"stop": stop_benchmark_server, "start": start_benchmark_server, "container": configs.EXPERIMENTS_CONTAINER},
        "inference": {"stop": stop_inference_server, "start": start_inference_server, "container": configs.INFERENCE_CONTAINER},
    }
    image = image_types[image_type]

    # Opening port initially to allow Docker to run
    make_docker_trusted = ssh_client.run_command(f"sudo firewall-cmd --permanent --zone=trusted --change-interface=docker0")
    for line in make_docker_trusted.stdout:
        print(line)

    # Logging in to authenticate pull
    login = ssh_client.run_command(f"sudo docker login {configs.FMAX_LOGIN_SERVER} --username {configs.FMAX_USERNAME} -p {configs.FMAX_PASSWORD}")
    for line in login.stdout: # printing output
        print(line)
    for line in login.stderr:
        print("docker login: ", line)

    # Pulling fmax-remote Docker image and inserting credentials in prompt
    pull_docker_hub = ssh_client.run_command(f'sudo docker pull {image["container"]}')

    for line in pull_docker_hub.stdout: # printing output
        print(line)
    for line in pull_docker_hub.stderr:
        print(line)

    # Starting the container
    running = image["start"](ssh_client)
    if running:
        # Stopping the container after a brief pause
        time.sleep(0.5)
        stopped = image["stop"](ssh_client)
        if stopped:
            success = True

    # Logging out to remove credentials from /root/.docker/config.json
    logout = ssh_client.run_command("sudo docker logout")
    for line in logout.stdout: # printing output
        print(line)
    for line in logout.stderr:
        print(line)

    return success
