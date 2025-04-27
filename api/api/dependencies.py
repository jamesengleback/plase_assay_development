from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from .model import engine


def common_parameters(offset: int = 0, limit: int = 100):
    return {"offset": offset, "limit": limit}


def get_session():
    with Session(engine) as session:
        yield session
