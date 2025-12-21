from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..dependencies import get_session, common_parameters
from ..model import Protein
from .serializers import ProteinReturnType

router = APIRouter()


@router.get("/")
async def get_protein(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    id: int | None = None,
    session: Session = Depends(get_session),
) -> ProteinReturnType | list[ProteinReturnType]:

    query = select(Protein)

    if id:
        query = query.where(Protein.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Protein with id {id} not found")
        return data

    query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()
    return data
