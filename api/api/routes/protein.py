from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..dependencies import get_session, common_parameters
from ..model import Protein
from .serializers import ProteinReturnType

router = APIRouter()

@router.get("/")
def get_protein(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    id: int | None = None,
    session: Session = Depends(get_session),
) -> list[ProteinReturnType]:

    query = select(Protein)

    if id:
        query = query.where(Protein.id == id)

    query = query.offset(common_parameters['offset']).limit(common_parameters['limit'])
    data = session.exec(query)
    return data
