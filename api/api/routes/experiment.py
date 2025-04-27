from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..model import Experiment, Result, engine
from ..dependencies import get_session, common_parameters
from .serializers import ExperimentSummaryReturnType, ExperimentDetailReturnType


router = APIRouter()


@router.get("/")
def get_experiments(common_parameters: Annotated[dict, Depends(common_parameters)],
                    session: Session = Depends(get_session),
                    id: str | None = None,
                    ) -> list[ExperimentSummaryReturnType]:
    query = select(Experiment)
    data = session.exec(query).all()
    return data


@router.get("/{id}")
def get_experiment(common_parameters: Annotated[dict, Depends(common_parameters)],
                   session: Session = Depends(get_session),
                   id: str | None = None,
                   ) -> ExperimentDetailReturnType:
    query = select(Experiment).where(Experiment.id == id)
    query = query.options(
        selectinload(Experiment.plates),
        selectinload(Experiment.results)#.selectinload(Result.test_wells),
    )
    data = session.exec(query).first()
    # for result in data.results:
    #     total_well_vols = [i.total_volume for i in result.test_wells]
    #     assert len(set(total_well_vols)) == 1
    #     vol = total_well_vols[0]
    #     result.well_volume = vol
    #     # attach to return type
    if data is None:
        raise HTTPException(status_code=404)
    return data
