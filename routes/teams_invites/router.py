from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime

from db_crudbase.pyobjectid import PyObjectId
from utils.auth_handler import auth_handler
from utils.email_handler import send_email
from routes import utils as route_utils

from database import user_crud, team_member_crud, teams_crud, invites_crud
from _templates import HTML_INVITE, TEXT_INVITE
from .schemas import *


router = APIRouter(prefix='/teams', tags=['teams - invites'])


@router.post('/{team_id}/members/invite')
def invite_team_members(team_id: str, request: Request, data: InviteUser, user: auth_handler.auth_wrapper = Depends()):
    team_member = route_utils.verify_team_member_exists(team_id, user["_id"])
    team_id = PyObjectId(team_id)
    new_user = None

    # check verified roles
    if data.role not in ["admin", "collaborator"]:
        raise HTTPException(status_code=403, detail="Invalid role selected.")

    # collaborators can only invite collaborators
    if team_member["role"] == "collaborator" and data.role != "collaborator":
        raise HTTPException(status_code=403, detail="Unauthorized.")

    # verify user isn't part of the team
    invitee_user = user_crud.get({"email": data.email})
    if invitee_user is not None:
        invitee = team_member_crud.get({"team_id": team_id, "user_id": invitee_user["_id"]})

        # invitee is already part of the team
        if invitee is not None:
            raise HTTPException(status_code=403, detail="Invitee is already a team member")
        
    else:
        # create new user
        password = auth_handler.get_password_hash("123456measure")
        new_user = user_crud.create({"first_name": "new", "last_name": "invitee", "password": password, "email": data.email, "date_created": datetime.now()})
        
        # add to team
        team_member_crud.create({"team_id": team_id, "user_id": new_user["_id"], "role": data.role})

    # get email content
    frontend_url = dict(request.scope["headers"]).get(b"referer", b"").decode()  # get url of the client making the request
    team = teams_crud.get_by_id(team_id)

    subject = f"{user['first_name']} invited you to join their team on Measure!"
    html_message = HTML_INVITE.replace('<frontend_url>', frontend_url).replace('<username>', user['first_name']).replace('<team_name>', team["name"])
    text_message = TEXT_INVITE.replace('<frontend_url>', frontend_url).replace('<username>', user['first_name']).replace('<team_name>', team["name"])

    # send email
    send_email(subject, data.email, text_content=text_message, html_content=html_message)

    # add invite to db
    invites_crud.create({
        "sender_id": user["_id"],  "invitee": data.email, "team_id": team["_id"], 
        "role": data.role, "date_created": datetime.now().strftime('%m-%d-%Y %H:%M:%S'),
        "status": "pending"
    })
    return {'message': 'OK'}


@router.get('/{team_id}/members/invites')
def get_sent_invites(team_id: str, user: auth_handler.auth_wrapper = Depends()):
    """
    this gets all the invites sent by this user
    """
    team = route_utils.verify_team_exists(team_id)

    invites = invites_crud.get_all({"sender_id": user["_id"], "team_id": team["_id"]})
    for i in invites:
        i.update({"sender": user})
    return invites 


@router.get('/{team_id}/members/invite/{invite_id}')
def get_invite(team_id: str, invite_id: str, user: auth_handler.auth_wrapper = Depends()):
    team = route_utils.verify_team_exists(team_id)

    invite = invites_crud.get({"sender_id": user["_id"], "team_id": team["_id"], "_id": PyObjectId(invite_id)})
    return invite


@router.post('/{team_id}/members/invite/{invite_id}/{invite_choice}')
def handle_invite(invite_choice: str, team_id: str, invite_id: str, user: auth_handler.auth_wrapper = Depends()):
    
    # verify invite choice
    invite_choice = invite_choice.lower()
    if invite_choice not in ['accept', 'decline']:
        raise HTTPException(403, detail="unknown choice")
    
    # verify team
    team = route_utils.verify_team_exists(team_id)

    # verify invite exists
    invite = invites_crud.get({"team_id": team["_id"], "_id": PyObjectId(invite_id)})
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite does not exist")

    # verify user is invitee via email
    if user["email"] != invite["invitee"]:
        raise HTTPException(status_code=400, detail="Unauthoried")        
    
    # handle invite based on choice
    if invite_choice == 'accept':
        # add to team member
        team_member_crud.create({"user_id": user["_id"], "team_id": team["_id"], "role": invite["role"]})

        # update invite db
        invites_crud.update({"is_closed": True, "status": "joined"}, invite["_id"])
    
    else:
        member = team_member_crud.get({"user_id": user["_id"], "team_id": team["_id"]})
        if member is not None:
            team_member_crud.delete(member["_id"])
            
        invites_crud.update({"is_closed": True, "status": "declined"}, invite["_id"])
        
    return 1


@router.delete('/{team_id}/members/invite/{invite_id}')
def delete_team_invite(team_id: str, invite_id: str, _: auth_handler.auth_wrapper = Depends()):
    route_utils.verify_team_exists(team_id)

    invites_crud.delete(invite_id)
    return 1
