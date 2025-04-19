from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from ..model import Absorbance, engine
from .serializers import AbsorbanceReturnType


router = APIRouter()


@router.get('/')
@router.get('/{id}')
def get_absorbance(id: str | None = None,
              well_id: int | None = None,
              ) -> list[AbsorbanceReturnType]:
    query = select(Absorbance)
    if id is not None:
        query = query.where(Absorbance.id == id)
    elif well_id is not None:
            query = query.where(Absorbance.well_id == well_id)
    with Session(engine) as session:
        data = session.exec(query).all()
    return data

