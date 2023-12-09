from pydantic import BaseModel
from typing import Optional


class CreateICDataset(BaseModel):
    annotations: Optional[str] = None
    images: Optional[str] = None
    name: str


class CreateLlamaDataset(BaseModel):
    name: str
    question_key: str
    correct_response_key: str
    incorrect_response_key: Optional[str] = None
