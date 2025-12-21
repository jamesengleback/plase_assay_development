from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import NonNegativeFloat
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, cast, String

import numpy as np
import utils
from ..model import (
    engine,
    Result,
    Absorbance,
    Well,
    DoseResponse,
    ResultAnnotation,
    WellResultLink,
    Compound,
    Protein,
)
from ..dependencies import get_session, common_parameters
from .serializers import ResultReturnType, ResultDetailReturnType, AbsorbanceReturnType


router = APIRouter()


@router.get("/")
async def get_results(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    id: int | None = None,
    experiment_id: int | None = None,
    locked: bool | None = None,
    accepted: bool | None = None,
    protein: str | None = None,
    well_volume_min: float | None = None,
    well_volume_max: float | None = None,
    protein_concentration_min: float | None = None,
    protein_concentration_max: float | None = None,
    search: str | None = None,
    session: Session = Depends(get_session),
) -> ResultReturnType | list[ResultReturnType]:

    query = select(Result).options(
        selectinload(Result.annotations),
        selectinload(Result.dose_response),
        selectinload(Result.compound),
        selectinload(Result.protein),
    )

    if id:
        query = query.where(Result.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Result with id {id} not found")
        return data
    elif experiment_id:
        query = query.where(Result.experiment_id == experiment_id)

    if locked is not None:
        query = query.where(Result.locked == locked)
    if accepted is not None:
        query = query.where(Result.accepted == accepted)
    if protein:
        query = query.join(Result.protein).where(
            Protein.name.ilike(f"%{protein}%")
        )

    if protein_concentration_min is not None:
        query = query.where(Result.protein_concentration >= protein_concentration_min)
    if protein_concentration_max is not None:
        query = query.where(Result.protein_concentration <= protein_concentration_max)

    # Join with wells for filtering on well properties
    if well_volume_min is not None or well_volume_max is not None:
        query = query.join(WellResultLink, WellResultLink.result_id == Result.id).join(Well, WellResultLink.well_id == Well.id)
        if well_volume_min is not None:
            query = query.where(Well.volume >= well_volume_min)
        if well_volume_max is not None:
            query = query.where(Well.volume <= well_volume_max)
        query = query.distinct()

    if search:
        query = query.join(Compound, Result.compound_id == Compound.id, isouter=True).where(
            or_(
                cast(Result.id, String).ilike(f"%{search}%"),
                Compound.name.ilike(f"%{search}%")
            )
        )

    query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()
    return data


@router.get("/{id}")
async def get_result(
    id: int | None = None, session: Session = Depends(get_session)
) -> ResultDetailReturnType:

    # statement = (
    #     select(Result, WellResultLink, Well, Absorbance)
    #     .join(Well, WellResultLink.well_id == Well.id)
    #     .join(Absorbance, WellResultLink.well_id == Absorbance.well_id) # Assuming Well.id links to Absorbance.well_id
    #     .where(WellResultLink.result_id == id)
    # )

    query = (
        select(Result)
        .join(WellResultLink)
        .options(
            selectinload(Result.dose_response),
            selectinload(Result.compound),
            selectinload(Result.protein),
            # (
            # selectinload(Result.wells)
            # .options(
            #     selectinload(Well.plate_data_file),
            #          )
            # # .options(selectinload(WellResultLink.well_type))
            # ),
        )
        .where(Result.id == id)
    )

    data = session.exec(query).first()
    if data is None:
        raise HTTPException(status_code=404, detail=f'Result(id={id}) not found')

    return data


@router.patch("/{id}")
async def patch_result(
    id: int | None,
    accept: Annotated[bool | None, Form()] = None,
    lock: Annotated[bool | None, Form()] = None,
    comment: Annotated[str | None, Form()] = None,
    exclude_id: Annotated[int | None, Form()] = None,
    exclude: Annotated[bool | None, Form()] = None,
    session: Session = Depends(get_session),
) -> ResultReturnType | None:

    result = session.get(Result, id)

    if result is None:
        raise HTTPException(status_code=404)

    if accept is not None:
        result.accepted = accept
        session.add(result)
        session.commit()
        session.refresh(result)
        return result

    if lock is not None:
        result.locked = lock
        session.add(result)
        session.commit()
        session.refresh(result)
        return result

    if comment:
        annotation = ResultAnnotation(
            result_id=result.id,
            comment=comment,
        )
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
        session.refresh(result)
        return result

    if exclude_id is not None:
        dose_response = session.get(DoseResponse, exclude_id)
        if dose_response is None:
            raise HTTPException(
                status_code=404, detail=f"DoseResponse(id={exclude_id}) not found"
            )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Result(id={id}) not found")

        dose_response.exclude = exclude
        session.add(dose_response)
        session.commit()
        session.refresh(dose_response)

        xy = [
            [d.concentration, d.response] for d in result.dose_response if not d.exclude
        ]
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
    raise HTTPException(status_code=400)
