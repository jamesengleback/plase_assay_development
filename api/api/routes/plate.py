from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..model import Plate
from ..dependencies import get_session, common_parameters
from .serializers import PlateReturnType


router = APIRouter()


@router.get("/")
@router.get("/{id}")
async def get_plate(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: int | None = None,
    experiment_id: int | None = None,
) -> PlateReturnType | list[PlateReturnType]:
    query = select(Plate)
    if id is not None:
        query = query.where(Plate.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Plate with id {id} not found")
        return data
    else:
        if experiment_id is not None:
            query = query.where(Plate.experiment_id == experiment_id)
        query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
        data = session.exec(query).all()
    return data
