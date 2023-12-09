from fastapi import APIRouter, HTTPException, Depends

from database import user_crud, team_member_crud

from utils.auth_handler import auth_handler
from db_crudbase.pyobjectid import PyObjectId
from routes import utils as route_utils

from .schemas import *


router = APIRouter(prefix='/teams', tags=['teams - members'])


@router.get('/{team_id}/members')
def get_members(team_id: str, user: auth_handler.auth_wrapper = Depends()):
    route_utils.verify_team_member_exists(team_id, user["_id"])

    # get all members
    teams_members = team_member_crud.get_all({"team_id": PyObjectId(team_id)})

    # get user info
    team_members = []
    for member in teams_members:
        user = user_crud.get_by_id(member["user_id"])
        user_info = {
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": member["role"],
            "_id": user["_id"]
        }
        team_members.append(user_info)

    return team_members


@router.put('/{team_id}/members/{member_id}')
def update_members_role(team_id: str, member_id: str, data: UpdateMembersRole, user: auth_handler.auth_wrapper = Depends()):
    team_member = route_utils.verify_team_member_exists(team_id, user["_id"])

    # check verified roles
    if data.role not in ["admin", "collaborator"]:
        raise HTTPException(status_code=400, detail="Invalid role selected.")

    # dissalow collaborators
    if team_member["role"] == "collaborator":
        raise HTTPException(status_code=403, detail="Unauthorized.")

    # get member
    member = team_member_crud.get({"team_id": PyObjectId(team_id),
                                   "user_id": PyObjectId(member_id)})
    if member is None:
        raise HTTPException(status_code=403, detail="Member does not exist")

    # verify not owner
    if member["role"] == 'owner':
        raise HTTPException(status_code=403, detail="Cannot edit owner")

    # update member
    team_member_crud.update({"role": data.role}, member_id)
    return member_id


@router.delete('/{team_id}/members/{member_id}')
def delete_members(team_id: str, member_id: str, user: auth_handler.auth_wrapper = Depends()):
    team_member = route_utils.verify_team_member_exists(team_id, user["_id"])

    # dissalow collaborators
    if team_member.role == "collaborator":
        raise HTTPException(status_code=403, detail="Unauthorized.")

    # get member
    member = team_member_crud.get({"team_id": PyObjectId(team_id),
                                   "user_id": PyObjectId(member_id)})
    if member is None:
        raise HTTPException(status_code=403, detail="Member does not exist")

    # verify not owner
    if member["role"] == 'owner':
        raise HTTPException(status_code=403, detail="Cannot remove admin")

    # verify not admins
    if team_member["role"] == 'admin' and member["role"] == 'admin':
        raise HTTPException(status_code=403, detail="Cannot remove admin")

    # update member
    team_member_crud.delete(member_id)
    return member_id
