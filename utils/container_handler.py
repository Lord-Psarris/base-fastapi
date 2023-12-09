import configs
import pssh


def handle_stdin_response(command_result):
    if command_result is None:
        return False
    
    for i in command_result.stderr:
        print("Error:", i)
        return False
        
    return True


def handle_commands(ssh_client, command):
    try:
        command_result = ssh_client.run_command(command)
        return command_result
    
    except pssh.exceptions.SessionError:
        print("---- could not access server ----")
    
    except Exception as e:
        print(e)
        
    return None
    


def start_benchmark_server(ssh_client):
    """
    Starts the benchmark server container.
    """
    command_result = handle_commands(ssh_client, 
                                    command=f"sudo docker run -dp {configs.EXPERIMENTS_PORT}:{configs.EXPERIMENTS_PORT} {configs.EXPERIMENTS_CONTAINER}")        
    return handle_stdin_response(command_result)


def stop_benchmark_server(ssh_client):
    """
    Stops the benchmark server container.
    """
    command_result = handle_commands(ssh_client, 
                                    command=f"sudo docker stop $(sudo docker ps -a -q --filter ancestor={configs.EXPERIMENTS_CONTAINER}) && sudo docker rm $(sudo docker ps -a -q --filter ancestor={configs.EXPERIMENTS_CONTAINER})")
    return handle_stdin_response(command_result)


def start_inference_server(ssh_client):
    """
    Starts the inference remote container.
    """
    command_result = ssh_client.run_command(f"sudo docker run -dp {configs.INFERENCE_PORT}:{configs.INFERENCE_PORT} {configs.INFERENCE_CONTAINER}")
    return handle_stdin_response(command_result)


def stop_inference_server(ssh_client):
    """
    Stops the inference remote container.
    """
    command_result = ssh_client.run_command(f"sudo docker stop $(sudo docker ps -a -q --filter ancestor={configs.INFERENCE_CONTAINER}) && sudo docker rm $(sudo docker ps -a -q --filter ancestor={configs.INFERENCE_CONTAINER})")
    return handle_stdin_response(command_result)
