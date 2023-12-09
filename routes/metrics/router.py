from fastapi import APIRouter, Depends

from utils.auth_handler import auth_handler
from . import utils as metrics_utils


router = APIRouter(prefix='/metrics', tags=['metrics - data'])


@router.get('')
def get_metrics(user: auth_handler.auth_wrapper = Depends()):
    user_metrics = {}
    user_id = user["_id"]
    
    # get env metrics
    environment_metrics = metrics_utils.get_environment_metrics(user_id)
    
    # get experiment metrics
    experiment_metrics = metrics_utils.get_experiment_metrics(user_id)
    
    # get dataset metrics
    dataset_metrics = metrics_utils.get_dataset_metrics(user_id)
    
    # get model metrics
    model_metrics = metrics_utils.get_model_metrics(user_id)

    # format retrieved metrics
    for metric in [experiment_metrics, model_metrics, environment_metrics, dataset_metrics]:
        user_metrics.update(metric)

    return user_metrics
