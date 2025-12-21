from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from ..model import Well, Compound, Protein, Absorbance
from ..dependencies import get_session, common_parameters
from .serializers import WellReturnType, WellDetailReturnType


router = APIRouter()


@router.get("/")
@router.get("/{id}")
async def get_well(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: str | None = None,
    plate: int | None = None,
) -> WellReturnType | list[WellReturnType]:
    query = select(Well)
    if id is not None:
        query = query.where(Well.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Well with id {id} not found")
        return data
    else:
        if plate is not None:
            query = query.where(Well.plate_id == plate)
        query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
        data = session.exec(query).all()
        return data


@router.get("/{id}/detail")
async def get_well_detail(id: int, session: Session = Depends(get_session)) -> WellDetailReturnType:
    query = (
        select(Well)
        .where(Well.id == id)
        .options(selectinload(Well.absorbance), selectinload(Well.compound))
    )
    well = session.exec(query).first()
    if not well:
        raise HTTPException(status_code=404)
    return well
