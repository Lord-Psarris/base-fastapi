from auth_client.fastapi_utils.token_validators import decode_token
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import Optional

from utils.auth_handler import ad_client, ad_b2c_client, auth_handler
from database import user_crud
from .schemas import *

import configs

router = APIRouter(prefix='/auth', tags=['auth - sso'])


# create login link
@router.get('/login')
def get_login_link(request: Request, auth_method: Optional[str] = 'b2c'):
    app_url = dict(request.scope["headers"]).get(b"referer", b"").decode()
    if app_url[-1] == "/":
        app_url = app_url.rstrip(app_url[-1])

    redirect_url = f"{app_url}/receive-token"
    if auth_method == 'b2c':
        return ad_b2c_client.generate_auth_url(redirect_url=redirect_url)
        
    return ad_client.generate_login_url(redirect_url=redirect_url)


# verify generated code
@router.get('/validate-token')
def verify_token(code: str, request: Request, auth_method: Optional[str] = 'b2c'):
    app_url = dict(request.scope["headers"]).get(b"referer", b"").decode()
    if app_url[-1] == "/":
        app_url = app_url.rstrip(app_url[-1])

    if auth_method == 'b2c':
        token = ad_b2c_client.validate_auth_code(code, redirect_url=f"{app_url}/receive-token")
    else:
        token = ad_client.validate_auth_code(code, redirect_url=f"{app_url}/receive-token")
        
    # handle error
    if "error" in token:
        raise HTTPException(400, detail=token["description"])
        
    valid_token_data = decode_token(token["id_token"], client_id=configs.CLIENT_ID)
    unique_name = valid_token_data.get('preferred_username')
    emails = valid_token_data.get('emails', [None])
    
    email = unique_name if unique_name else emails[0]
    
    # verify user exists
    user = user_crud.get({"email": email})
    if user is None:
        raise HTTPException(403, detail="user doesn't exist")

    # generate token
    token = auth_handler.encode_token(str(user["_id"]))
    return token


@router.post('/sign-up')
def sign_up(data: CreateUser):

    # verify user doesn't exist
    existing_user = user_crud.get({"email": data.email})
    if existing_user is not None:
        raise HTTPException(403, detail="account already exists")

    # parse data to dict
    data = data.dict()

    # encrypt password
    data["password"] = auth_handler.get_password_hash(data["password"])

    # set date created
    data["date_created"] = datetime.now()

    # upload data
    new_user = user_crud.create(data)
    return new_user


@router.post('/sign-in')
def sign_in(data: LoginUser):

    # verify user exists
    user = user_crud.get({"email": data.email})
    if user is None:
        raise HTTPException(403, detail="user doesn't exist")

    # verify password
    if not auth_handler.verify_password(data.password, user["password"]):
        raise HTTPException(403, detail="incorrect password")

    # generate token
    token = auth_handler.encode_token(str(user["_id"]))
    return token


# verify user is authenticated
@router.get('/is-authed')
async def verify_user_token(user_id: auth_handler.auth_wrapper_decode_token = Depends()):
    """
    This returns a boolean specifying if the token provided is valid
    """
    is_authed = user_id if user_id else False
    if is_authed:
        user = user_crud.get_by_id(user_id)
        return user

    return False
