from pydantic import BaseModel
from typing import Optional


class CreateTeam(BaseModel):
    name: str
    description: str


class UodateTeam(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
