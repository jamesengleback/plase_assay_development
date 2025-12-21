from sqlmodel import Session, select
from sqlalchemy import func
from api.model import Experiment, Result, Plate, engine
from api.routes.serializers import ExperimentSummaryReturnType

with Session(engine) as session:
    query = select(Experiment, func.count(Plate.id).label('num_plates'), func.count(Result.id).label('num_results')).outerjoin(Plate, Plate.experiment_id == Experiment.id).outerjoin(Result, Result.experiment_id == Experiment.id).group_by(Experiment.id)
    data = session.exec(query).all()
    print("Data length:", len(data))
    if len(data) > 0:
        row = data[0]
        exp, num_p, num_r = row
        print("num_p:", num_p, "num_r:", num_r)
        ret = ExperimentSummaryReturnType(**exp.__dict__, num_plates=num_p, num_results=num_r)
        print("Return type:", ret)