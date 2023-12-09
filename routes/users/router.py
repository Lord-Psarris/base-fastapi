from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from database import user_crud, invites_crud
from utils.auth_handler import auth_handler
from .schemas import *

router = APIRouter(prefix='/users', tags=['users - details'])


@router.get('')
def get_details(user: auth_handler.auth_wrapper = Depends()):
    return user


@router.put('/update-details')
def update_user_details(data: UpdateUser, user: auth_handler.auth_wrapper = Depends()):
    user_crud.update(data.dict(), user["_id"])
    return 1


@router.put('/update-password')
def update_password(data: UpdatePassword, user: auth_handler.auth_wrapper = Depends()):

    if data.new_password == data.old_password:
        raise HTTPException(403, detail='old password must not be same as new password')

    # verify old password
    if not auth_handler.verify_password(data.old_password, user["password"]):
        raise HTTPException(403, detail="incorrect password")
    
    # parse to dict & encrypt password
    new_password = auth_handler.get_password_hash(data.new_password)

    user_crud.update({"password": new_password}, user["_id"])

    token = auth_handler.encode_token(str(user["_id"]))
    return {"message": "OK", "token": token}


@router.get('/invites')
def get_received_invites(user: auth_handler.auth_wrapper = Depends()):
    """
    this gets all the invites sent by this user
    """
    invites = invites_crud.get_all({"invitee": user["email"]})
    for i in invites:
        i.update({"sender": user})
    return invites 
