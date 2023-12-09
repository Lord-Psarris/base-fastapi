from pydantic import BaseModel
from typing import Optional


class CreateProject(BaseModel):
    name: str
    description: str
    team_id: Optional[str] = None


class UpdateProject(CreateProject):
    ...
