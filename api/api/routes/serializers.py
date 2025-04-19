import datetime
from pydantic import BaseModel
from ..model import Experiment, Plate, Result, AssayMixDispenseMethod, LigandDispenseMethod, BindingExperiment, Absorbance

class CompoundReturnType(BaseModel):
    id: int
    canonical_smiles: str | None
    name: str | None
    svg: str | None
    mw: float | None


class PlateReturnType(BaseModel):
    id: int
    plate_data_file_id: int | None
    # plate_data_file: PlateDataFile
    product_name: str | None
    # wells: list[Well]
    experiment_id: int | None
    # experiment: Experiment


class WellReturnType(BaseModel):
    id: int | None
    plate_id: int | None
    # plate: PlateReturnType
    address: str | None

    # compound_id: int | None
    # compound: CompoundReturnType | None
    compound_concentration: float | None

    protein_id: int | None
    # protein: Protein | None
    protein_concentration: float | None

    total_volume: float | None

    file_id: int | None
    # file: 'PlateDataFile'

    result_id: int | None
    # result: 'Result'

    # absorbance: list[Absorbance]
    # annotations: list['WellAnnotation']


class AbsorbanceReturnType(BaseModel):
    id: int

    plate_data_file_id: int | None
    # plate_data_file: 'PlateDataFile'
    well_id: int | None

    wavelength: float | None
    absorbance: float | None


class WellDetailReturnType(BaseModel):
    id: int | None
    plate_id: int | None
    address: str | None

    compound_id: int | None
    compound: CompoundReturnType | None
    compound_concentration: float | None

    protein_id: int | None
    # protein: Protein | None
    protein_concentration: float | None

    total_volume: float | None

    file_id: int | None
    # file: 'PlateDataFile'

    result_id: int | None
    # result: 'Result'
    absorbance: list[AbsorbanceReturnType]
    class Config:
        orm_mode = True


class ExperimentReturnType(BaseModel):
    id: int | None
    plates: list[Plate]
    results: list[Result]
    binding_experiments: list['BindingExperiment']
    start_date: datetime.datetime | None
    dispense_assay_mix: AssayMixDispenseMethod | None
    dispense_ligands: LigandDispenseMethod | None
    centrifuge_minutes: int | None
    centrifuge_rpm: int | None
    protein_days_thawed: int | None



