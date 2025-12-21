from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from sqlmodel import Session, select
from ..model import Experiment, Result, Plate, engine
from ..dependencies import get_session, common_parameters
from .serializers import ExperimentSummaryReturnType, ExperimentDetailReturnType


router = APIRouter()


@router.get("/")
async def get_experiments(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: str | None = None,
) -> list[ExperimentSummaryReturnType]:
    query = select(Experiment, func.count(func.distinct(Plate.id)).label('num_plates'), func.count(func.distinct(Result.id)).label('num_results')).outerjoin(Plate, Plate.experiment_id == Experiment.id).outerjoin(Result, Result.experiment_id == Experiment.id).group_by(Experiment.id).offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()
    return [ExperimentSummaryReturnType(**exp.__dict__, num_plates=num_p, num_results=num_r) for exp, num_p, num_r in data]


@router.get("/{id}")
async def get_experiment(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: str | None = None,
) -> ExperimentDetailReturnType:
    query = select(Experiment).where(Experiment.id == id)
    data = session.exec(query).first()
    if data is None:
        raise HTTPException(status_code=404)
    return data
