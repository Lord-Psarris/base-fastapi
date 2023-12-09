from pydantic import BaseModel


class ProvisionEnvironment(BaseModel):
    name: str
    model_id: str
    model_is_pretrained: bool
    environment_id: str


class AddProvisionEnvironmentModel(BaseModel):
    model_id: str
    model_is_pretrained: bool
