from pydantic import BaseModel
from typing import Optional

 
class CreateBenchmarkExperiment(BaseModel):
    environment_id: str
    batchsize: int
    project_id: str
    model_id: str
    dataset: str
    name: str
