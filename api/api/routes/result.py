from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import NonNegativeFloat
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

import numpy as np
import utils
from ..model import engine, Result, Absorbance, Well, DoseResponse, ResultAnnotation
from ..dependencies import get_session, common_parameters
from .serializers import ResultReturnType, ResultDetailReturnType, AbsorbanceReturnType


router = APIRouter()


@router.get("/")
def get_results(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    id: int | None = None,
    experiment_id: float | None = None,
    session: Session = Depends(get_session),
) -> list[ResultReturnType]:

    query = select(Result)

    if id:
        query = query.where(Result.id == id)
    elif experiment_id:
        query = query.where(Result.experiment_id == id)

    query = query.options(
        selectinload(Result.dose_response),
        selectinload(Result.compound),
    )

    query = query.offset(common_parameters['offset']).limit(common_parameters['limit'])
    data = session.exec(query)
    return data


@router.get("/{id}")
def get_result(
    id: int | None = None,
    session: Session = Depends(get_session)
) -> ResultDetailReturnType:
    query = select(Result).where(Result.id == id)
    query = query.options(
        selectinload(Result.dose_response),
        selectinload(Result.compound),
        selectinload(Result.test_wells).options(  # Load related PlateDataFile for Wells
            selectinload(Well.plate_data_file)
        ),
        # selectinload(Result.control_wells),
    )

    data = session.exec(query).first()
    return data


@router.patch("/{id}")
def patch_result(
    id: int | None,
    accept: Annotated[bool, Form()] = None,
    exclude_id: Annotated[int, Form()] = None,
    exclude: Annotated[bool, Form()] = None,
    comment: Annotated[str, Form()] = None,
    session: Session = Depends(get_session)
        ) -> ResultReturnType:

    result = session.get(Result, id)

    if result is None:
        raise HTTPException(status_code=404)

    if accept:
        result.accepted = accept
        session.add(result)
        session.commit()
        session.refresh(result)
        return result

    if comment:
        annotation = ResultAnnotation(result_id=result.id,
                                      comment=comment,
                                      )
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
        session.refresh(result)
        return result

    dose_response = session.get(DoseResponse, exclude_id)
    if dose_response is None:
        raise HTTPException(status_code=404, detail=f'DoseResponse(id={exclude_id}) not found')
    if result is None:
        raise HTTPException(status_code=404, detail=f'Result(id={id}) not found')

    dose_response.exclude = exclude
    session.add(dose_response)
    session.commit()
    session.refresh(dose_response)

    xy = [[d.concentration, d.response] for d in result.dose_response if not d.exclude]
    x = np.array([d[0] for d in xy])
    y = np.array([d[1] for d in xy])

    vmax, km = utils.mm.calculate_km(y, x)
    r_squared = utils.mm.r_squared(y, utils.mm.curve(x, vmax, km))

    result.km = km
    result.vmax = vmax
    result.r_squared = r_squared

    session.add(result)
    session.commit()
    session.refresh(result)

    return result
