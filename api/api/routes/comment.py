from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from ..model import ResultAnnotation, engine
from ..dependencies import get_session, common_parameters
from .serializers import ResultAnnotationReturnType

router = APIRouter()


@router.post("/")
def post_comment(result_id: Annotated[int, Form()],
                 comment: Annotated[str, Form()],
                 session: Session = Depends(get_session),
                 ) -> ResultAnnotationReturnType:

    comment = ResultAnnotation(result_id=result_id, comment=comment)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

@router.get("/")
@router.get("/{id}")
def get_comment(session: Session = Depends(get_session),
                id: str | None = None,
                result_id: int | None = None,
                ) -> list[ResultAnnotationReturnType]:

    query = select(ResultAnnotation)

    if result_id:
        query = query.where(ResultAnnotation.result_id == result_id)
    elif id:
        query = query.where(ResultAnnotation.id == id)

    data = session.exec(query).all()

    return data

@router.delete("/{id}")
def delete_comment(session: Session = Depends(get_session),
                id: str | None = None,
                ) -> None:
    annotation = session.get(ResultAnnotation, id)
    if not annotation:
        raise HTTPException(status_code=404)
    session.delete(annotation)
    session.commit()
    return None

