from pydantic import BaseModel
from typing import Optional


class CreateFinetuneExperiment(BaseModel):
    environment_id: str
    project_id: str
    dataset_id: str
    model_id: str
    name: str
    

class CreateFinetuneRun(BaseModel):
    epochs: int = 3
    test_size: float = 0.2
    train_size: float = 0.8
    batchsize: Optional[int] = 2
    