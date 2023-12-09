from fastapi import File, HTTPException
from pssh.clients import SSHClient
from datetime import datetime
from typing import Optional

from utils.os_handler.ubuntu import run_setup_ubuntu
from utils.os_handler.centos import run_setup_centos


def setup_environment(ssh_client: SSHClient, environment_data: dict, ssh_key: Optional[File], os_name: str):
    # Gathering hardware information
    cpu_name, cpu_cores, memory_total = get_unix_cpu_ram(ssh_client)

    # update request data
    environment_data["cores"] = cpu_cores
    environment_data["processor"] = cpu_name
    environment_data["ram_gb"] = memory_total
    environment_data["use_pkey"] = ssh_key != None
    environment_data["date_created"] = datetime.now().timestamp()

    # delete unwanted keys
    del environment_data["ssh_key"]

    # Setting up the remote host
    if os_name == "Ubuntu":
        setup_status = run_setup_ubuntu(ssh_client, cpu_name)
        
    elif os_name == "CentOS Linux":
        setup_status = run_setup_centos(ssh_client, cpu_name)
        
    else:
        raise HTTPException(status_code=500, detail="Environment OS not supported")
        
    if setup_status == "failed":
        raise HTTPException(status_code=500, detail="Environment setup failed.")

    # Returning the  environment data
    environment_data["status"] = "success"
    return environment_data



def get_unix_cpu_ram(ssh_client: SSHClient):
    """
    Gets CPU and RAM information from a Unix client.
    """
    # Gathering CPU info
    cpu_info = ssh_client.run_command("cat /proc/cpuinfo")
    cpu_name = ""
    cpu_cores = ""
    # stdout is a generator (cannot directly access indexes)
    for line in cpu_info.stdout:
        # Taking model name line from output for CPU name and extracting name only
        if "model name" in line:
            cpu_name = line.split(":")[1].strip()
        # Taking cpu cores line from output for CPU cores
        if "cpu cores" in line:
            cpu_cores = line.split(":")[1].strip()

    # Gathering RAM info
    ram_info = ssh_client.run_command("cat /proc/meminfo")
    memory_total = ""
    # stdout is a generator (cannot directly access indexes)
    for line in ram_info.stdout:
        # Taking MemTotal line from output and processing it for exact Kb value
        if "MemTotal" in line:
            memory_total = line.split()[1].strip()
            break

    # Some additional work to turn the kb value from memory_total into gb
    print(memory_total)
    memory_total = round(int(memory_total) / 1000000)

    print(f"CPU: {cpu_name}", f"CORES: {cpu_cores}", f"MEM: {memory_total} gb")
    return cpu_name, cpu_cores, memory_total
