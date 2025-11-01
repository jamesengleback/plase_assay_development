from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from ..model import Plate, engine
from .serializers import PlateReturnType


router = APIRouter()


@router.get("/")
@router.get("/{id}")
def get_plate(
    id: int | None = None,
    experiment: int | None = None,
) -> list[PlateReturnType]:
    query = select(Plate)
    if id is not None:
        query = query.where(Plate.id == id)
    else:
        if experiment is not None:
            query = query.where(Plate.experiment_id == experiment)
    with Session(engine) as session:
        data = session.exec(query).all()
    return data
