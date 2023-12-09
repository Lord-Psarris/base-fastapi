from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from database.schemas import CreateUser, LoginUser
from utils.auth_handler import auth_handler
from database import Users

router = APIRouter(prefix='/auth', tags=['auth - sso'])


@router.post('/sign-up')
def sign_up(data: CreateUser):

    # verify user doesn't exist
    existing_user = Users.get({"email": data.email})
    if existing_user is not None:
        raise HTTPException(403, detail="account already exists")

    # parse data to dict
    data = data.dict()

    # encrypt password
    data["password"] = auth_handler.get_password_hash(data["password"])

    # set date created
    data["date_created"] = datetime.now()

    # upload data
    new_user = Users.create(data)
    return new_user


@router.post('/sign-in')
def sign_in(data: LoginUser):

    # verify user exists
    user = Users.get({"email": data.email})
    if user is None:
        raise HTTPException(403, detail="user doesn't exist")

    # verify password
    if not auth_handler.verify_password(data.password, user["password"]):
        raise HTTPException(403, detail="incorrect password")

    # generate token
    token = auth_handler.encode_token(str(user["_id"]))
    return token


# verify user is authenticated
@router.get('/is-valid')
async def verify_user_token(user_id: auth_handler.auth_wrapper_decode_token = Depends()):
    """
    This returns a boolean specifying if the token provided is valid
    """
    is_authed = user_id if user_id else False
    if is_authed:
        user = Users.get_by_id(user_id)
        return user

    return False
