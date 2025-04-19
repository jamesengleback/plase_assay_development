from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from . import model
from . import routes

api = FastAPI()

api.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        # allow_credentials=False,
        # allow_methods=['*'],
        # allow_headers=['*'],
        )

api.include_router(routes.result.router,
                   prefix='/result'
                   )

api.include_router(routes.experiment.router,
                   prefix='/experiment')

api.include_router(routes.plate.router,
                   prefix='/plate'
                   )

api.include_router(routes.well.router,
                   prefix='/well'
                   )

api.include_router(routes.absorbance.router,
                   prefix='/absorbance'
                   )


@api.on_event('startup')
def init_db():
    SQLModel.metadata.create_all(model.engine)
