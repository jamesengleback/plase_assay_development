from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from ..model import Experiment, engine


router = APIRouter()


@router.get('/')
def get_experiment(id: str | None = None) -> list[Experiment]:
    query = select(Experiment)
    if id is not None:
        query = query.where(Experiment.id == id)
    with Session(engine) as session:
        data =  session.exec(query).all()
    return data
