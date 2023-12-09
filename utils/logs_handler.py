from datetime import datetime

from utils.container_handler import handle_commands
from database import logs_crud
import configs


def log_experiment(ssh_client, endpoint: str, environment_id: str, timestamp: str):
    print("---- logging experiment ----")
    
    # get logs from remote machine
    command_result = handle_commands(ssh_client, command=f"sudo docker logs $(sudo docker ps -a -q --filter ancestor={configs.EXPERIMENTS_CONTAINER}) --timestamps --since={timestamp}")
    logs = []
    for i in command_result.stdout:
        logs.append(str(i))
        
    for i in command_result.stderr:
        logs.append(str(i))
    
    # store in db
    logs_crud.create({
        "logs": logs,
        "endpoint": endpoint,
        "created_on": datetime.now(),
        "environment_id": environment_id,
    })

    return logs
