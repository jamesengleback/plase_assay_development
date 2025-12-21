from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..model import ResultAnnotation, Result, engine
from ..dependencies import get_session, common_parameters
from .serializers import ResultAnnotationReturnType

router = APIRouter()


@router.post("/")
def post_comment(
    result_id: Annotated[int, Form()],
    comment: Annotated[str, Form()],
    session: Session = Depends(get_session),
) -> ResultAnnotationReturnType:
    result = session.get(Result, result_id)
    if not result.locked:
        annotation = ResultAnnotation(result_id=result_id, comment=comment)
        session.add(annotation)
        session.commit()
        session.refresh(annotation)
        return annotation
    else:
        raise HTTPException(status_code=403, detail="Result is locked")


@router.get("/")
@router.get("/{id}")
def get_comment(
    common_parameters: Annotated[dict, Depends(common_parameters)],
    session: Session = Depends(get_session),
    id: str | None = None,
    result_id: int | None = None,
) -> ResultAnnotationReturnType | list[ResultAnnotationReturnType]:
    query = select(ResultAnnotation)

    if result_id:
        query = query.where(ResultAnnotation.result_id == result_id)
    elif id:
        query = query.where(ResultAnnotation.id == id)
        data = session.exec(query).first()
        if not data:
            raise HTTPException(status_code=404, detail=f"Comment with id {id} not found")
        return data

    query = query.offset(common_parameters["offset"]).limit(common_parameters["limit"])
    data = session.exec(query).all()

    return data


@router.delete("/{id}")
def delete_comment(
    session: Session = Depends(get_session),
    id: str | None = None,
) -> None:
    annotation = session.get(ResultAnnotation, id)
    if not annotation:
        raise HTTPException(status_code=404)
    if not annotation.result.locked:
        session.delete(annotation)
        session.commit()
        return None
    else:
        raise HTTPException(status_code=403, detail="Result is locked")
