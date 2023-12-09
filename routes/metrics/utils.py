from typing import Union
from db_crudbase.pyobjectid import PyObjectId

from configs.modellibrary import MODELS as pretrained_models
from database import *


def get_environment_metrics(user_id: Union[str, PyObjectId]) -> dict:
    # all environments
    environments = environments_crud.get_all({"user_id": user_id})
    
    # provisioned environments
    provisioned_environments = list(filter(lambda x: x.get("is_provisioned", False), environments))

    # intel environments
    intel_environments = list(filter(lambda x: 'intel' in x["processor"].lower(), environments))

    # amd environments
    amd_environments = list(filter(lambda x: 'amd' in x["processor"].lower(), environments))

    return {
        "environments": {
            "total_provisioned_environments": len(provisioned_environments),
            "total_intel_environments": len(intel_environments),
            "total_amd_environments": len(amd_environments),
            "total_environments": len(environments),
        }
    }


def get_experiment_metrics(user_id: Union[str, PyObjectId]) -> dict:
    # all experiments
    benchmark_experiments = benchmarks_crud.get_all({"user_id": user_id})
    finetune_experiments = fine_tunings_crud.get_all({"user_id": user_id})
    
    all_experiments =  [*benchmark_experiments, *finetune_experiments]
    

    # pending experiments
    pending_experiments = list(filter(lambda x: x["status"].lower() == 'processing', all_experiments))
    
    # executed experiments
    executed_experiments = list(filter(lambda x: x["status"].lower() == 'executed', all_experiments))
    
    # failed
    failed_experiments = list(filter(lambda x: x["status"].lower() == 'failed', all_experiments))
    
    return {
        "experiments": {
            "total_experiments": len(all_experiments),
            "total_failed_experiments": len(failed_experiments),
            "total_pending_experiments": len(pending_experiments),
            "total_executed_experiments": len(executed_experiments),
            "total_finetune_experiments": len(finetune_experiments),
            "total_benchmark_experiments": len(benchmark_experiments),
        }
    }


def get_model_metrics(user_id: Union[str, PyObjectId]) -> dict:
    # all models
    uploaded_models = uploaded_models_crud.get_all({"user_id": user_id})
    
    # finetuned models
    finetuned_models = finetuned_models_crud.get_all({"user_id": user_id})
    
    return {
        "models": {
            "total_uploaded_models": len(uploaded_models),
            "total_finetuned_models": len(finetuned_models),
            "total_pretrained_models": len(pretrained_models),
            "total_models": len([*uploaded_models, *finetuned_models, *pretrained_models])
        }
    }


def get_dataset_metrics(user_id: Union[str, PyObjectId]) -> dict:
    # all datasets
    datasets = datasets_crud.get_all({"user_id": user_id})
    
    # image classification datasets
    ic_datasets = list(filter(lambda x: "image-classification" == x["type"], datasets))
    
    # llama datasets
    llama_datasets = list(filter(lambda x: "generative-text" == x["type"], datasets))
    
    # library datasets
    library_datasets = list(filter(lambda x: x["use_from_library"], datasets))
    
    return {
        "datasets": {
            "total_datasets": len(datasets),
            "total_ic_datasets": len(ic_datasets),
            "total_llama_datasets": len(llama_datasets),
            "total_library_datasets": len(library_datasets)
        }
    }
