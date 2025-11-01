from enum import Enum
import datetime
from sqlmodel import Field, SQLModel, Relationship, create_engine
from sqlalchemy import UniqueConstraint


class Protein(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str | None # = Field(index=True)
    sequence: str | None
    purification: str | None
    # __table_args__ = (UniqueConstraint("name"),)


class Compound(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    canonical_smiles: str | None
    name: str | None
    svg: str | None
    mw: float | None


class Absorbance(SQLModel, table=True):
    id: int | None = Field(primary_key=True)

    plate_data_file_id: int | None = Field(foreign_key="platedatafile.id")
    plate_data_file: "PlateDataFile" = Relationship(back_populates="absorbances")
    well_id: int | None = Field(foreign_key="well.id")
    well: "Well" = Relationship(back_populates="absorbance")

    wavelength: float | None
    absorbance: float | None


class Well(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    plate_id: int | None = Field(foreign_key="plate.id")
    plate: "Plate" = Relationship(back_populates="wells")
    address: str | None

    compound_id: int | None = Field(foreign_key="compound.id")
    compound: Compound | None = Relationship()
    compound_concentration: float | None

    protein_id: int | None = Field(foreign_key="protein.id")
    protein: Protein | None = Relationship()
    protein_concentration: float | None

    volume: float | None

    plate_data_file_id: int | None = Field(foreign_key="platedatafile.id")
    plate_data_file: "PlateDataFile" = Relationship(back_populates="wells")

    absorbance: list[Absorbance] = Relationship(back_populates="well")
    annotations: list["WellAnnotation"] = Relationship(back_populates="well")


class WellAnnotation(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    well_id: int | None = Field(foreign_key="well.id")
    well: Well | None = Relationship(back_populates="annotations")
    comment: str | None
    exclude: bool | None

    a_800: float | None
    auc: float | None
    k: float | None
    rsq: float | None


class Plate(SQLModel, table=True):
    id: int = Field(primary_key=True)
    # experiment_id: int | None = Field(default=None, primary_key=True)
    plate_data_file_id: int | None = Field(foreign_key="platedatafile.id")
    product_name: str | None
    label: str | None
    wells: list[Well] = Relationship(back_populates="plate")
    experiment_id: int | None = Field(foreign_key="experiment.id")
    experiment: "Experiment" = Relationship()


class PlateDataFile(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    plate: Plate = Relationship()
    absorbances: list[Absorbance] = Relationship(back_populates="plate_data_file")
    wells: list[Well] = Relationship(back_populates="plate_data_file")
    results: list["Result"] = Relationship(back_populates="plate_data_file")

    created_at: datetime.date | None
    path: str
    hash: str = Field(index=True)
    parse_error: bool


class DoseResponse(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    concentration: float
    response: float
    result_id: int = Field(foreign_key="result.id")
    result: "Result" = Relationship(back_populates="dose_response")
    exclude: bool = False

    test_well_id: int | None = Field(foreign_key="well.id")
    test_well: Well | None = Relationship(
            sa_relationship_kwargs={
            "foreign_keys": "DoseResponse.test_well_id", 
        }
            )

    control_well_id: int | None = Field(foreign_key="well.id")
    control_well: Well | None = Relationship(
            sa_relationship_kwargs={
            "foreign_keys": "DoseResponse.control_well_id", 
        }
            )


class WellTypeEnum(Enum):
    control = 'control'
    test = 'test'


class WellDoseResponseLink(SQLModel, table=True):
    well_id: int | None = Field(
        default=None, foreign_key="well.id", primary_key=True
    )
    well_type: WellTypeEnum


class WellResultLink(SQLModel, table=True):
    well_id: int | None = Field(
        default=None, foreign_key="well.id", primary_key=True
    )
    result_id: int | None = Field(
        default=None, foreign_key="result.id", primary_key=True
    )
    well_type: WellTypeEnum


class Result(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # binding_experiment_id: int | None = Field(foreign_key='bindingexperiment.id')
    # binding_experiment: 'BindingExperiment' = Relationship(back_populates='result')



    # result: Result | None = Relationship(back_populates='binding_experiment')
    # well_volume: int | None
    compound: Compound | None = Relationship()
    compound_id: int | None = Field(foreign_key="compound.id")
    experiment: "Experiment" = Relationship(back_populates="results")
    experiment_id: int | None = Field(foreign_key="experiment.id")
    plate: Plate | None = Relationship()
    plate_data_file: PlateDataFile | None = Relationship(back_populates="results")
    plate_data_file_id: int | None = Field(foreign_key="platedatafile.id")
    plate_id: int | None = Field(foreign_key="plate.id")
    protein: Protein | None = Relationship()
    protein_concentration: float | None
    protein_id: int | None = Field(foreign_key="protein.id")
    result_id: int | None = Field(foreign_key="result.id")
    wells: list[Well] | None = Relationship(link_model=WellResultLink)

    k: float | None
    km: float | None
    vmax: float | None
    r_squared: float | None

    # a420_max: float | None
    # auc_mean: float | None
    # auc_cv: float | None
    # std_405: float | None
    # dd_soret: float | None

    locked: bool | None
    accepted: bool | None
    annotations: list["ResultAnnotation"] = Relationship(back_populates="result")
    dose_response: list[DoseResponse] = Relationship(back_populates="result")


class ResultAnnotation(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    result_id: int = Field(foreign_key="result.id")
    result: Result = Relationship(back_populates="annotations")
    comment: str | None


class LigandDispenseMethod(Enum):
    echo = "echo"
    serial_dilution = "serial_dilution"


class AssayMixDispenseMethod(Enum):
    electronic_multichannel_pipette = "electronic_multichannel_pipette"
    peristaltic_pump = "multidrop"


class Experiment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    plates: list[Plate] = Relationship(back_populates="experiment")
    results: list[Result] = Relationship(back_populates="experiment")

    start_date: datetime.datetime | None
    dispense_assay_mix: AssayMixDispenseMethod | None
    dispense_ligands: LigandDispenseMethod | None
    centrifuge_minutes: int | None
    centrifuge_rpm: int | None
    protein_days_thawed: int | None


# class BindingExperiment(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#
#     experiment_id: int | None = Field(foreign_key="experiment.id")
#     experiment: Experiment = Relationship()
#     protein_id: int | None = Field(foreign_key="protein.id")
#     protein: Protein | None = Relationship()
#     compound_id: int | None = Field(foreign_key="compound.id")
#     compound: Compound | None = Relationship()
#     plate_id: int | None = Field(foreign_key="plate.id")
#     plate: Plate | None = Relationship()
#     result_id: int | None = Field(foreign_key="result.id")
#     # result: Result | None = Relationship(back_populates='binding_experiment')


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)
