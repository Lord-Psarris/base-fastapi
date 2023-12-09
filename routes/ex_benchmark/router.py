from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from database import experiments_crud, benchmarks_crud, uploaded_models_crud, environments_crud
from routes import utils as route_utils

from utils.experiments_handler.benchmark import run_benchmark
from utils.auth_handler import auth_handler
from .schemas import *


router = APIRouter(prefix='/experiments/benchmark', tags=['experiments - benchmark'])


@router.get("")
def get_benchmarks(recent: Optional[bool] = False, user: auth_handler.auth_wrapper = Depends()):
    benchmarks = sorted(benchmarks_crud.get_all({"user_id": user["_id"]}), 
                        key=lambda x: x["created_on"], reverse=True)
    if recent:  # handle recent query
        benchmarks = benchmarks[:5]

    # set model
    for benchmark in benchmarks:
        benchmark["model"] = uploaded_models_crud.get_by_id(benchmark["model_id"])
        benchmark["environment"] = environments_crud.get_by_id(benchmark["environment_id"])

    return benchmarks


@router.get("/{benchmark_id}")
def get_benchmark_item(benchmark_id: str, user: auth_handler.auth_wrapper = Depends()):
    benchmark = benchmarks_crud.get({"user_id": user["_id"], "_id": benchmark_id})
    benchmark["model"] = uploaded_models_crud.get_by_id(benchmark["model_id"])
    benchmark["environment"] = environments_crud.get_by_id(benchmark["environment_id"])

    return benchmark


@router.post("")
def create_benchmark(data: CreateBenchmarkExperiment, user: auth_handler.auth_wrapper = Depends()):
    data.name = data.name.replace(" ", "_")
    
    # verify benchmark doesn't exist
    existing_benchmark = benchmarks_crud.get({"user_id": user["_id"], "name": data.name})
    if existing_benchmark is not None:
        raise HTTPException(403, detail="benchmark already exists")

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
    benchmarks_crud.create(data)
    return 1


@router.get('/{benchmark_id}/experiments')
def get_benchmark_experiments(benchmark_id: str, user: auth_handler.auth_wrapper = Depends()):

    # verify benchmark exists
    benchmark = benchmarks_crud.get({"user_id": user["_id"], "_id": benchmark_id})
    if benchmark is None:
        raise HTTPException(403, detail="benchmark does not exists")
    
    experiments = experiments_crud.get_all({"type": "benchmark", "experiment_id": benchmark_id})
    return sorted(experiments, key=lambda x: x.get("created_on", 1), reverse=True)


@router.post('/{benchmark_id}/experiment')
def run_benchmark_experimet(benchmark_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get benchmark
    benchmark = benchmarks_crud.get({"_id": benchmark_id, "user_id": user["_id"]})
    if benchmark is None:
        raise HTTPException(403, detail="This benchmark doesn't exist")

    # get environment data
    environment = environments_crud.get_by_id(benchmark["environment_id"])
    if environment is None:
        raise HTTPException(403, detail="This environment doesn't exist")
    
    # update benchmark
    benchmarks_crud.update({"status": "pending"}, benchmark_id)
    
    # set time last used to environment
    environments_crud.update({"last_used": datetime.now().timestamp()}, benchmark["environment_id"])

    # run benchmarking experiment
    response_data = run_benchmark(environment_data=environment, benchmark_data=benchmark)

    # Updating experiment result status 
    if response_data["is_successful"]:
        benchmarks_crud.update({"status": "executed"}, benchmark_id)
    else:
        benchmarks_crud.update({"status": "failed"}, benchmark_id)

    # save experiment run
    experiments_crud.create({
        "created_on": datetime.now().timestamp(),
        "experiment_id": benchmark_id,
        "user_id": user["_id"],
        "type": "benchmark",
        **response_data
    })
    return response_data


@router.delete('/{benchmark_id}')
def delete_benchmark(benchmark_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get benchmark
    benchmark = benchmarks_crud.get({"_id": benchmark_id, "user_id": user["_id"]})
    if benchmark is None:
        raise HTTPException(403, detail="This benchmark doesn't exist")
    
    benchmarks_crud.delete(benchmark_id)
    return 1