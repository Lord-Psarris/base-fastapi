from pydantic import BaseModel


class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
    
    
class UpdateUser(BaseModel):
    first_name: str
    last_name: str
