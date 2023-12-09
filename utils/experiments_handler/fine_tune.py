from fastapi import HTTPException

from utils.remote_handler import run_remote_endpoint
from configs.modellibrary import MODELS
from database import datasets_crud


def run_fine_tuning_experiment(environment_data: dict, fine_tune_data: dict, epochs: int, test_size: float, train_size: float, batchsize: int):
    # get model type
    model = next(iter(filter(lambda x: x["_id"] == fine_tune_data["model_id"], MODELS)), None)
    if model is None:
        raise HTTPException(400, detail="model id is invalid")
    
    category = model['category']
    
    # get dataset
    dataset = datasets_crud.get_by_id(fine_tune_data["dataset_id"])
    
    # creating request body
    request_body = {
        "epochs": epochs,
        "test_size": test_size,
        "train_size": train_size,
        "dataset": dataset["name"],
        "user_id": fine_tune_data["user_id"],
        "training_id": fine_tune_data["_id"],
        "from_library": dataset["use_from_library"]
    }
    
    # update dataset accordingly
    if category == "generative-text":
        request_body.update({
            "question_key": dataset["question_key"],
            "correct_response_key":  dataset["correct_response_key"],
            "incorrect_response_key": dataset["incorrect_response_key"],
        })
        
    else:  # image classification
        request_body.update({
            "model_id":  fine_tune_data["model_id"],
            "annotations": dataset["annotations"],
            "images":  dataset["images"],
            "batchsize": batchsize
        })
    
    # the experiment is completed
    return run_remote_endpoint(environment_data, request_body, endpoint=f"fine-tune/{category}")
