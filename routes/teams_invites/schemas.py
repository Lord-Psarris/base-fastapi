from pydantic import BaseModel, EmailStr


class UpdateMembersRole(BaseModel):
    role: str


class InviteUser(BaseModel):
    email: EmailStr
    role: str
