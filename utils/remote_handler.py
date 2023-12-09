from requests.exceptions import ConnectionError
from datetime import datetime

from utils.connection_handler import connect_to_host_with_pkey, connect_to_host_with_password
from utils.container_handler import start_benchmark_server, stop_benchmark_server
from utils.logs_handler import log_experiment

import requests
import time


def run_remote_endpoint(environment_data: dict, request_data: dict, endpoint: str, port: int = 4000):
    """
    Sends an HTTP request to some host in order to run a model benchmark.
    """
    # set result dict
    result = {
        "response": {},
        "is_successful": False
    }

    # Grabbing required environment details
    hostname = environment_data["hostname"]
    user = environment_data["username"]

    if environment_data["use_pkey"]:
        # If connecting via a private key
        ssh_client = connect_to_host_with_pkey(hostname=hostname, user=user, environment_id=environment_data["_id"])
    else:
        # If connecting via a password
        ssh_client = connect_to_host_with_password(hostname=hostname, user=user, environment_id=environment_data["_id"])
        
    # handle ssh_client error
    if ssh_client is None:
        result["response"] = "an error occured while connecting to the host"
        return result

    stop_benchmark_server(ssh_client)
    measure_is_running = start_benchmark_server(ssh_client)
    print("---- measure_is_running ----", measure_is_running)

    if not measure_is_running:
        stop_benchmark_server(ssh_client)
        return result
    
    # create start timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
    # Retrying the post 5 times to compensate for slow Docker starts
    for _ in range(5):
        try:
            response = requests.post(f"http://{hostname}:{port}/{endpoint}", json=request_data)
            # response = requests.post(f"http://localhost:{port}/{endpoint}", json=request_data)
            
            if response.status_code != 200:
                result["response"] = response.json().get("detail", response.json())
                
                stop_benchmark_server(ssh_client)
                print("---- measure_is_stopping ----")
                break
                
            # set result
            result["response"] = response.json()
            result["is_successful"] = True
            
            # stop measure
            stop_benchmark_server(ssh_client)
            print("---- measure_is_stopping ----")
            
            # return/break on success
            break
        
        except ConnectionError as error:
            time.sleep(60)
            continue # Retries on connection fails only

        except Exception as error:
            print(error)

            stop_benchmark_server(ssh_client)
            result["response"] = str(error)
            return result

        finally:
            time.sleep(15)
            log_experiment(ssh_client, endpoint, environment_data["_id"], timestamp)
    
    # the experiment is completed
    return result
