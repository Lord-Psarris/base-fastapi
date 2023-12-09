from fastapi import HTTPException
from typing import Union

from database import teams_crud, team_member_crud, projects_crud
from db_crudbase.pyobjectid import PyObjectId


# teams
def verify_team_exists(team_id: str) -> dict:
    """
    this function checks if a team exists, and raises an error if it soesn't
    """
    team = teams_crud.get_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=403, detail="This team doesn't exist")
    
    return team


def verify_team_member_exists(team_id: Union[str, PyObjectId], user_id: Union[str, PyObjectId]) -> dict:
    """
    this function checks if a team member exists in a team, and raises an error if it soesn't
    """
    team_id = PyObjectId(team_id)
    team = verify_team_exists(team_id)

    team_member = team_member_crud.get({"team_id": team["_id"], "user_id": PyObjectId(user_id)})
    if team_member is None:
        raise HTTPException(status_code=403, detail="You are not a member of this team")
    
    return team_member


def verify_project_exists(project_id: Union[str, PyObjectId]) -> dict:
    """
    this function checks if a project exists, and raises an error if it soesn't
    """
    project = projects_crud.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="This project doesn't exist")
    
    return project
    

def verify_user_project_permissions(user_id: Union[str, PyObjectId], project: dict):
    has_permissions = False

    # if project has a team verify user role on team, otherwise verify user created project
    if project["team_id"] is not None:
        # get team member
        team_member = verify_team_member_exists(project["team_id"], user_id)

        # verify roles
        if team_member["role"] == 'owner' or team_member["role"] == 'admin':
            has_permissions = True

    elif project["user_id"] == user_id:
        has_permissions = True

    return has_permissions
    




        