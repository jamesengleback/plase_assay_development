import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.api import api
from api.dependencies import get_session
from api.model import engine as prod_engine


@pytest.fixture(scope="session")
def test_engine():
    # Use in-memory SQLite for tests to avoid affecting production DB
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    from sqlmodel import Session
    SessionLocal = Session
    session = SessionLocal(test_engine)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    # Override the session dependency
    def override_get_session():
        return db_session

    api.dependency_overrides[get_session] = override_get_session
    with TestClient(api) as test_client:
        yield test_client
    api.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_data(db_session):
    # Create sample data for testing
    from api.model import Experiment, Protein, Compound, Well, Result, WellResultLink, WellTypeEnum

    # Create test entities
    exp1 = Experiment()
    exp2 = Experiment()
    prot1 = Protein(name="BM3 WT")
    prot2 = Protein(name="Protein B")
    comp1 = Compound(name="Compound X")
    comp2 = Compound(name="Compound Y")

    well1 = Well(volume=50.0, protein_concentration=1.0)
    well2 = Well(volume=100.0, protein_concentration=2.0)
    well3 = Well(volume=75.0, protein_concentration=1.5)

    db_session.add_all([exp1, exp2, prot1, prot2, comp1, comp2, well1, well2, well3])
    db_session.flush()

    # Create results
    result1 = Result(
        experiment_id=exp1.id,
        protein_id=prot1.id,
        compound_id=comp1.id,
        protein_concentration=1.0,
        locked=False,
        accepted=True
    )
    result2 = Result(
        experiment_id=exp1.id,
        protein_id=prot2.id,
        compound_id=comp2.id,
        protein_concentration=2.0,
        locked=True,
        accepted=False
    )
    result3 = Result(
        experiment_id=exp2.id,
        protein_id=prot1.id,
        compound_id=comp1.id,
        protein_concentration=1.5,
        locked=False,
        accepted=True
    )

    db_session.add_all([result1, result2, result3])
    db_session.flush()

    # Link wells to results
    link1 = WellResultLink(well_id=well1.id, result_id=result1.id, well_type=WellTypeEnum.test)
    link2 = WellResultLink(well_id=well2.id, result_id=result2.id, well_type=WellTypeEnum.test)
    link3 = WellResultLink(well_id=well3.id, result_id=result3.id, well_type=WellTypeEnum.test)

    db_session.add_all([link1, link2, link3])
    # No commit

    return {
        "experiments": [exp1, exp2],
        "proteins": [prot1, prot2],
        "compounds": [comp1, comp2],
        "wells": [well1, well2, well3],
        "results": [result1, result2, result3]
    }