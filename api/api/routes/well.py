from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from ..model import Well, engine, Compound, Protein, Absorbance
from .serializers import WellReturnType, WellDetailReturnType


router = APIRouter()


@router.get("/")
@router.get("/{id}")
async def get_well(
    id: str | None = None,
    plate: int | None = None,
) -> list[WellReturnType]:
    query = select(Well)
    if id is not None:
        query = query.where(Well.id == id)
    else:
        if plate is not None:
            query = query.where(Well.plate_id == plate)
    with Session(engine) as session:
        data = session.exec(query).all()
        return data


@router.get("/{id}/detail")
async def get_well_detail(id: int) -> WellDetailReturnType:
    with Session(engine) as session:
        # well = session.get(Well, id)
        query = (
            select(Well)
            .where(Well.id == id)
            .options(selectinload(Well.absorbance), selectinload(Well.compound))
        )
        well = session.exec(query).first()
        if not well:
            raise HTTPException(status_code=404)
        return well
