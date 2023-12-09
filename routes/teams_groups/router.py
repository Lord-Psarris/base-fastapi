from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from database import projects_crud, teams_crud, team_member_crud
from utils.auth_handler import auth_handler
from db_crudbase.pyobjectid import PyObjectId

from .schemas import *


router = APIRouter(prefix='/teams', tags=['teams - groups'])


@router.get('/')
def get_user_teams(user: auth_handler.auth_wrapper = Depends()):
    # get all team member instances
    teams_members = team_member_crud.get_all({"user_id": user["_id"]})

    teams = []
    for i in teams_members:
        team = teams_crud.get_by_id(i["team_id"])
        teams.append(team)

    return teams


@router.get('/{team_id}')
def get_user_team(team_id: str, user: auth_handler.auth_wrapper = Depends()):
    team_id=PyObjectId(team_id)
    
    # verify the user is on this team
    teams_member = team_member_crud.get({"user_id": user["_id"], "team_id": team_id})
    if teams_member is None:
        raise HTTPException(403, detail="user not part of the team")
    
    return teams_crud.get_by_id(team_id)


@router.get('/{team_id}/projects')
def get_team_projects(team_id: str, user: auth_handler.auth_wrapper = Depends()):
    team_id = PyObjectId(team_id)
    
    # get all team member instances
    teams_member = team_member_crud.get({"user_id": user["_id"], "team_id": team_id})
    if teams_member is None:
        raise HTTPException(403, detail="user not part of the team")

    projects = projects_crud.get_all({"team_id": team_id})
    return projects


@router.post('/')
def create_team(data: CreateTeam, user: auth_handler.auth_wrapper = Depends()):
    data = data.dict()
    data['created_at'] = datetime.now().strftime('%m-%d-%Y %H:%M:%S')

    new_team = teams_crud.create(data)
    team_member_crud.create({"user_id": user["_id"], "team_id": new_team["_id"], "role": "owner"})

    return new_team


@router.put('/{team_id}')
def update_team(team_id: str, data: UodateTeam, user: auth_handler.auth_wrapper = Depends()):
    data = data.dict()
    team_id = PyObjectId(team_id)

    # verify user role
    team_member = team_member_crud.get({"user_id": user["_id"], "team_id": team_id})
    if team_member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this team")

    # verify user role
    if team_member["role"] != "owner":
        raise HTTPException(status_code=403, detail="Unauthorized.")
    
    # remove None items
    cleaned_data = {}
    for k, v in data.items():
        if v is None:
            continue

        cleaned_data[k] = v

    # update team
    teams_crud.update(cleaned_data, team_id)
    return team_id


@router.delete('/{team_id}')
def delete_team(team_id: str, user: auth_handler.auth_wrapper = Depends()):
    team_id = PyObjectId(team_id)
    
    # verify user role
    team_member = team_member_crud.get({"user_id": user["_id"], "team_id": team_id})
    if team_member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this team")

    # verify user role
    if team_member["role"] != "owner":
        raise HTTPException(status_code=403, detail="Unauthorized.")

    # delete team
    teams_crud.delete(team_id)
    return team_id
