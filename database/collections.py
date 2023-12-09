from dotenv import load_dotenv
from pymongo import MongoClient
from db_crudbase import CRUDBase

import configs
import os

load_dotenv()

# setup mongo db
CLIENT = MongoClient(os.getenv('MONGO_DB_URL'))
DB = CLIENT.FMAX_DEV if configs.DEBUG_MODE else CLIENT.FMAX

# generate main cruds
user_crud = CRUDBase(collection_name="users", db=DB)
teams_crud = CRUDBase(collection_name="teams", db=DB)
invites_crud = CRUDBase(collection_name="invites", db=DB)
projects_crud = CRUDBase(collection_name="projects", db=DB)
team_member_crud = CRUDBase(collection_name="team_members", db=DB)
environments_crud = CRUDBase(collection_name="environments", db=DB)

# models
uploaded_models_crud = CRUDBase(collection_name="uploaded_models", db=DB)
finetuned_models_crud = CRUDBase(collection_name="finetuned_models", db=DB)

# for experiments
datasets_crud = CRUDBase(collection_name="datasets", db=DB)
benchmarks_crud = CRUDBase(collection_name="benchmarks", db=DB)
experiments_crud = CRUDBase(collection_name="experiments", db=DB)  # previously runs
fine_tunings_crud = CRUDBase(collection_name="fine_tunings", db=DB)
provisioned_environments_crud = CRUDBase(collection_name="provisioned_environments", db=DB)

# generate mini cruds
ssh_crud = CRUDBase(collection_name='ssh_keys', db=DB)
openvpn_crud = CRUDBase(collection_name='openvpn_certs', db=DB)

logs_crud = CRUDBase(collection_name='logs', db=DB)