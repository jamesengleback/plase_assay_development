from fastapi import APIRouter


router = APIRouter()


@router.get('/')
def get_result(id: str | None):
    pass
