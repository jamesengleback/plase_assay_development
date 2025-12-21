from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from .model import engine


def common_parameters(page: int = 1, limit: int = 100):
    offset = (page - 1) * limit
    return {"offset": offset, "limit": limit}


def get_session():
    with Session(engine) as session:
        yield session
