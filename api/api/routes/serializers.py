from typing import Optional
import datetime
from pydantic import BaseModel
from ..model import (
    Absorbance,
    # AssayMixDispenseMethod,
    DoseResponse,
    Experiment,
    LigandDispenseMethod,
    Plate,
    Protein,
    Result,
    ResultAnnotation,
    WellResultLink
)


class ProteinReturnType(BaseModel):
    id: int
    name: str
    sequence: str | None
    purification: str | None


class CompoundReturnType(BaseModel):
    id: int
    name: str | None

class CompoundVerboseReturnType(BaseModel):
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


class PlateDataFile(BaseModel):
    id: int
    plate: PlateReturnType | None
    path: str


class AbsorbanceReturnType(BaseModel):
    id: int

    # plate_data_file_id: int | None
    # plate_data_file: 'PlateDataFile'
    well_id: int | None

    wavelength: float | None
    absorbance: float | None


class DoseResponseReturnType(BaseModel):
    id: int | None
    concentration: float | None
    response: float | None
    exclude: bool | None


class WellReturnType(BaseModel):
    id: int | None
    plate_id: int | None
    address: str | None

    compound_id: int | None
    compound_concentration: float | None

    protein_id: int | None
    protein_concentration: float | None

    volume: float | None

    plate_data_file_id: int | None


class WellDetailReturnType(BaseModel):
    id: int | None
    plate_id: int | None
    address: str | None

    compound_id: int | None
    # compound: CompoundReturnType | None
    compound_concentration: float | None

    protein_id: int | None
    # protein: Protein | None
    protein_concentration: float | None

    volume: float | None

    plate_data_file_id: int | None
    # plate_data_file: 'PlateDataFile'

    # result_id: int | None
    # result: 'Result'
    absorbance: list[AbsorbanceReturnType]
    # well_result_link: WellResultLink
    # dose_response: list[DoseResponseReturnType]

    class Config:
        # orm_mode = True
        from_attributes = True


class ResultSummaryReturnType(BaseModel):
    experiment_id: int | None

    km: float | None
    vmax: float | None
    r_squared: float | None
    accepted: bool | None

    compound: CompoundReturnType | None
    protein: ProteinReturnType | None


class ResultAnnotationReturnType(BaseModel):
    id: int
    result_id: int
    comment: str | None


class ResultReturnType(BaseModel):
    id: int
    experiment_id: int | None
    accepted: bool | None
    active: bool | None
    locked: bool | None
    annotations: list[ResultAnnotationReturnType] | None

    km: float | None
    vmax: float | None
    r_squared: float | None

    dose_response: list[DoseResponseReturnType] | None
    compound: CompoundReturnType | None
    protein: ProteinReturnType | None
    protein_concentration: float | None


class ResultDetailReturnType(ResultReturnType):
    wells: list[WellDetailReturnType]


class ExperimentSummaryReturnType(BaseModel):
    id: int
    start_date: datetime.datetime | None
    dispense_assay_mix: str | None
    dispense_ligands: LigandDispenseMethod | None
    centrifuge_minutes: int | None
    centrifuge_rpm: int | None
    protein_days_thawed: int | None
    num_plates: int
    num_results: int

    class Config:
        from_attributes = True


class ExperimentDetailReturnType(BaseModel):
    id: int
    start_date: datetime.datetime | None
    dispense_assay_mix: str | None
    # dispense_assay_mix: AssayMixDispenseMethod | None
    dispense_ligands: LigandDispenseMethod | None
    centrifuge_minutes: int | None
    centrifuge_rpm: int | None
    protein_days_thawed: int | None
