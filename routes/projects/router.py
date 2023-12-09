from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from database import projects_crud, team_member_crud, fine_tunings_crud, benchmarks_crud, uploaded_models_crud, environments_crud, datasets_crud
from configs.modellibrary import MODELS as pretrained_models
from db_crudbase.pyobjectid import PyObjectId
from utils.auth_handler import auth_handler
from routes import utils as route_utils
from .schemas import *

router = APIRouter(prefix='/projects', tags=['projects - projects'])


@router.get('/')
def get_projects(user: auth_handler.auth_wrapper = Depends()):
    # get user projects
    user_projects = projects_crud.get_all({"user_id": user["_id"]})

    # get teams projects not created by the user
    user_teams = team_member_crud.get_all({"user_id": user["_id"]})
    team_projects = []

    for team_member in user_teams:
        
        # get all projects in this team
        projects = projects_crud.get_all({"team_id": team_member["team_id"]})

        # verify it isn't from this user and append
        projects = [i for i in projects if str(i["user_id"]) != str(user["_id"])]
        if not projects:
            continue
        
        team_projects.extend([i for i in projects])

    all_projects = user_projects + team_projects
    return all_projects


@router.get('/{project_id}')
def get_project(project_id: str, user: auth_handler.auth_wrapper = Depends()):
    project_id = PyObjectId(project_id)
    
    # get user projects
    project = projects_crud.get({"user_id": user["_id"], "_id": project_id})
    if project is not None:
        return project

    user_teams = team_member_crud.get_all({"user_id": user["_id"]})
    for team_member in user_teams:
        project = projects_crud.get({"team_id": team_member["_id"], "_id": project_id})
        if project is None:
            continue

        return project

    raise HTTPException(404, detail="project not found")
        


@router.post('/')
def create_project(data: CreateProject, user: auth_handler.auth_wrapper = Depends()):
    # verify team id exists
    if data.team_id:
        # verify user is authorized
        user_team = team_member_crud.get({"user_id": user["_id"], "team_id": PyObjectId(data.team_id)})
        if not user_team or user_team["role"] == "collaborator":
            raise HTTPException(status_code=401, detail="Unauthorized.")
        
        # make id valid
        data.team_id = PyObjectId(data.team_id)
    
    # add project to db
    data = data.dict()
    data["user_id"] = user["_id"]
    data["created_at"] = datetime.now().strftime('%m-%d-%Y %H:%M:%S')

    project = projects_crud.create(data)
    return project["_id"]


@router.put('/{project_id}')
def update_project(project_id: str, data: UpdateProject, user: auth_handler.auth_wrapper = Depends()):
    # get project 
    project = projects_crud.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project does not exist.")

    # verify user permissions
    has_permissions = route_utils.verify_user_project_permissions(user["_id"], project)
    if not has_permissions:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    # update project
    projects_crud.update(data.dict(), project["_id"])
    return project_id


@router.delete('/{project_id}')
def delete_project(project_id: str, user: auth_handler.auth_wrapper = Depends()):
    # get project 
    project = projects_crud.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project does not exist.")

    # verify user permissions
    has_permissions = route_utils.verify_user_project_permissions(user["_id"], project)
    if not has_permissions:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    projects_crud.delete(project_id)
    return project_id


@router.get('/{project_id}/experiments')
def get_project_experiments(project_id: str, _: auth_handler.auth_wrapper = Depends()):
    # get project 
    project = projects_crud.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project does not exist.")
    
    # set dataset & model name
    benchmarks = benchmarks_crud.get_all({"project_id": project["_id"]})
    for benchmark in benchmarks:
        benchmark["model"] = uploaded_models_crud.get_by_id(benchmark["model_id"])
        benchmark["environment"] = environments_crud.get_by_id(benchmark["environment_id"])
    
    fine_tunings = fine_tunings_crud.get_all({"project_id": project["_id"]})
    for fine_tuning in fine_tunings:
        fine_tuning["dataset"] = datasets_crud.get_by_id(fine_tuning["dataset_id"])
        fine_tuning["environment"] = environments_crud.get_by_id(fine_tuning["environment_id"])
        fine_tuning["model"] = next(filter(lambda x: x["_id"] == fine_tuning["model_id"], pretrained_models), None)
    
    return {
        "benchmarks": benchmarks,
        "fine_tunings": fine_tunings,
        "total_count": len(fine_tunings) + len(benchmarks)
    }
