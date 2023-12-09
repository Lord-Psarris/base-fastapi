from fastapi import FastAPI, APIRouter
from importlib import import_module
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

import os


def create_app(*args, **kwargs):
    app = FastAPI(*args, **kwargs)

    # setup cors
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # include routers
    include_routers(app, "routes")

    # mount static
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # setup api
    app.openapi = setup_open_api_config(app)
    return app


def include_routers(app: FastAPI, directory: str):
    """
    This function includes all routers in a directory to the app

    Args:
        app (FastAPI): _description_
        directory (str): _description_
    """
        
    routes_list = []    
    routers = []
    for path in os.listdir(directory):
        # verify filetype is a module directory
        if not os.path.isdir(f"{directory}/{path}"):
            continue
        
        routes_list.append(path)
        
    # parse routes
    for path in routes_list:
        # walk through files in dirs
        module = import_module(f"{directory}.{path}")
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, APIRouter):
                routers.append(obj)
        
    sorted_routes = sorted(routers, key=lambda x: x.tags[0])        
    for route in sorted_routes:
        app.include_router(route)


def setup_open_api_config(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title + " - Swagger UI",
            version="2.5.0",
            openapi_version="3.0.0",
            routes=app.routes,
        )

        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi
