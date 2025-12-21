from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..model import Absorbance
from ..dependencies import get_session, common_parameters
from .serializers import AbsorbanceReturnType


router = APIRouter()


@router.get("/")
@router.get("/{id}")
async def get_absorbance(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: str | None = None,
    well_id: int | None = None,
) -> AbsorbanceReturnType | list[AbsorbanceReturnType]:
    query = select(Absorbance)
    if id is not None:
        query = query.where(Absorbance.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Absorbance with id {id} not found")
        return data
    elif well_id is not None:
        query = query.where(Absorbance.well_id == well_id)
    
    query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()
    return data
