from utils.remote_handler import run_remote_endpoint


def run_benchmark(environment_data: dict, benchmark_data: dict):
    # Creating request body
    request_body = {
        "user_id": str(benchmark_data["user_id"]),
        "model_id": str(benchmark_data["model_id"]),
        "batch_sizes": benchmark_data["batchsize"],
        "dataset": benchmark_data["dataset"].lower(),
    }
    
    # the experiment is completed
    return run_remote_endpoint(environment_data, request_body, endpoint="benchmark")
