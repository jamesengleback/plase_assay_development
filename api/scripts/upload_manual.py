import sys
import math
import hashlib
import os
from string import ascii_uppercase
import re
import json
import logging
import datetime
import numpy as np
from sqlmodel import SQLModel, Session, select
from api import model
import utils
from upload_echo import PROTEINS, COMPOUNDS, well_ids, file_hash

logging.basicConfig(level=logging.INFO)

PROTEIN_NAME = "BM3 WT"


def main(args):
    with Session(model.engine) as session:
        protein = session.exec(
            select(model.Protein).where(model.Protein.name == PROTEIN_NAME)
        ).first()
        if protein is None:
            protein = model.Protein(
                name=PROTEIN_NAME,
                sequence=PROTEINS["BM3 WT"]["sequence"],
                purification="ni",
            )  # get or create
            session.add(protein)
            session.commit()
            session.refresh(protein)
        for config_path in args:
            logging.info(config_path)

            with open(config_path, "r") as f:
                config_data = json.load(f)

            experiment_number = config_data["experiment_number"]

            working_directory = os.path.abspath(os.path.dirname(config_path))
            constants = {
                i.lower(): j
                for i, j in zip(
                    config_data.keys(),
                    config_data.values(),
                )
                if not isinstance(j, (list, dict))
            }

            experiment = session.exec(
                select(model.Experiment).where(model.Experiment.id == experiment_number)
            ).first()
            if experiment is None:
                dispense_bulk = constants.get("dispense_bulk")
                if dispense_bulk is not None:
                    if dispense_bulk.lower() == "manual":
                        dispense_bulk = "electronic_multichannel_pipette"
                    elif dispense_bulk.lower() == "thermo multidrop combi":
                        dispense_bulk = "peristaltic_pump"
                dispense_ligands = constants.get("dispense_ligands")
                if dispense_ligands is not None:
                    if dispense_ligands.lower() == "serial dilution":
                        dispense_ligands = "serial_dilution"
                if dispense_ligands is not None:
                    dispense_ligands = dispense_ligands.lower()
                experiment = model.Experiment(
                    id=experiment_number,
                    start_date=datetime.date.fromisoformat(constants.get("start_date")),
                    dispense_ligands="serial_dilution",
                    dispense_assay_mix="electronic_multichannel_pipette",
                    centrifuge_minutes=0,
                    centrifuge_rpm=0,
                    protein_days_thawed=constants.get("protein_days_thawed"),
                )

            SQLModel.model_validate(experiment)
            session.add(experiment)

            test_rows = config_data["test_rows"]
            control_rows = config_data["control_rows"]
            concs = np.array(config_data["concentrations"])

            experiments = config_data.get("experiments")
            blocks = config_data.get("blocks")
            for plate_name in experiments.keys():
                experiment_config = experiments[plate_name]
                plate_data_path = os.path.join(
                    working_directory, experiment_config["file"]
                )
                logging.info(plate_data_path)
                img_dir = os.path.join(working_directory, "img")
                columns = experiment_config["columns"]

                plate = model.Plate(
                    label=plate_name,
                    experiment=experiment,
                    product_name=experiment_config.get("plate_type"),
                )

                session.add(plate)
                session.commit()
                session.refresh(plate)
                experiment.plates.append(plate)

                plate_data_file = model.PlateDataFile(
                    path=plate_data_path,
                    parse_error=False,
                )
                try:
                    session.add(plate_data_file)
                    session.commit()
                    session.refresh(plate_data_file)
                except Exception as e:
                    logging.warning(e)

                experiment_constants = {
                    i.lower(): j
                    for i, j in zip(
                        experiment_config.keys(),
                        experiment_config.values(),
                    )
                    if not isinstance(j, (list, dict))
                }

                protein_concentration = config_data.get("protein_concentration")

                df = utils.parse.bmg(plate_data_path)
                # df = df.subtract(df[800], axis=0) # 800 nm correction

                for column_num in columns:
                    column_data = columns[column_num]
                    independent_variables = (
                        constants
                        | experiment_constants
                        | {
                            i: column_data[i]
                            for i in column_data
                            if isinstance(column_data, dict)
                            and isinstance(column_data[i], (str, int, float))
                        }
                    )

                    if isinstance(column_data, str):
                        compound_name = (
                            column_data
                            if column_data
                            not in [
                                "Protein",
                                "Protein and DMSO",
                                "DMSO",
                            ]
                            else None
                        )
                    elif isinstance(column_data, dict):
                        compound_name = column_data.get("compound_name")
                        if not compound_name:
                            compound_name = column_data.get("ligand")
                    else:
                        raise Warning("Problem finding ligand")

                    compound = session.exec(
                        select(model.Compound).where(
                            model.Compound.name == compound_name
                        )
                    ).first()

                    if compound is None:
                        if compound_name:
                            compound_item = COMPOUNDS.get(compound_name.lower(), {})
                            compound = model.Compound(
                                name=compound_name,
                                canonical_smiles=compound_item.get("smiles"),
                                mw=compound_item.get("mw"),
                                svg=compound_item.get("svg"),
                            )

                    logging.info(
                        f"{experiment_number} {independent_variables.get('dispense_ligands')} {plate_name} column {column_num} ligand {compound_name}"
                    )

                    column_df = df.loc[df.index.str.contains(f"[A-Z]{column_num}$"), :]
                    if math.prod(column_df.dropna().shape) == 0:
                        logging.warn(f"No data for wells: {', '.join(column_df.index)}")
                        continue

                    test_data = column_df.loc[
                        column_df.index.str.contains("|".join(test_rows)), :
                    ]
                    control_data = column_df.loc[
                        column_df.index.str.contains("|".join(control_rows)), :
                    ]

                    test_wells = []
                    for conc, test_well_addr in zip(
                        concs,
                        test_data.index,
                    ):
                        test_well = model.Well(
                            plate=plate,
                            compound=compound,
                            protein=protein,
                            plate_data_file=plate_data_file,
                            protein_concentration=independent_variables.get(
                                "protein_concentration"
                            ),
                            compound_concentration=conc,
                            address=test_well_addr,
                            volume=independent_variables.get("well_volume"),
                        )

                        session.add(test_well)
                        session.commit()
                        session.refresh(test_well)
                        test_wells.append(test_well)

                        well_absorbance = df.loc[test_well_addr, :]

                        for wavelength, absorbance_value in zip(
                            well_absorbance.index, well_absorbance.values
                        ):
                            absorbance = model.Absorbance(
                                wavelength=wavelength,
                                absorbance=absorbance_value,
                                well_id=test_well.id,
                                plate_data_file_id=plate_data_file.id,
                            )
                            session.add(absorbance)
                        session.commit()

                    control_wells = []
                    for conc, control_well_addr in zip(concs, control_data.index):
                        control_well = model.Well(
                            plate=plate,
                            compound=compound,
                            protein=protein,
                            plate_data_file=plate_data_file,
                            protein_concentration=0,
                            compound_concentration=conc,
                            address=control_well_addr,
                            volume=independent_variables.get("well_volume"),
                        )

                        session.add(control_well)
                        session.commit()
                        session.refresh(control_well)
                        control_wells.append(control_well)

                        well_absorbance = df.loc[control_well_addr, :]

                        for wavelength, absorbance_value in zip(
                            well_absorbance.index, well_absorbance.values
                        ):
                            absorbance = model.Absorbance(
                                wavelength=wavelength,
                                absorbance=absorbance_value,
                                well_id=control_well.id,
                                plate_data_file_id=plate_data_file.id,
                            )
                            session.add(absorbance)
                        session.commit()
                    if control_well_addr:
                        corrected_data = test_data.reset_index(drop=True).subtract(
                            control_data.reset_index(drop=True)
                        )
                    else:
                        corrected_data = test_data

                    corrected_data = corrected_data.subtract(
                        corrected_data[800], axis=0
                    )

                    dose_responses = []
                    if concs is not None:
                        corrected_data = corrected_data.sort_index()
                        diff_data = corrected_data.subtract(
                            corrected_data.iloc[concs.argmin(), :], axis=1
                        )
                        response = utils.mm.calculate_response(diff_data)

                        try:
                            vmax, km = utils.mm.calculate_km(response, concs)
                            r_squared = utils.mm.r_squared(
                                response, utils.mm.curve(concs, vmax, km)
                            )
                            # Normalize vmax by a420_max of control (concentration = 0)
                            corrected_data.index = concs
                            a420_max_control = corrected_data.loc[concs.min(), 420]
                            if a420_max_control and a420_max_control > 0:
                                vmax = vmax / a420_max_control
                            for conc_i, response_i, test_well, control_well in zip(
                                concs, response, test_wells, control_wells
                            ):
                                test_well = session.refresh(test_well)
                                control_well = session.refresh(control_well)
                                dose_response = model.DoseResponse(
                                    concentration=conc_i,
                                    response=response_i,
                                    test_well=test_well,
                                    control_well=control_well,
                                )
                                # session.add(dose_response)
                                # session.refresh(dose_response)
                                dose_responses.append(dose_response)
                        except Exception as e:
                            logging.warning(f"Could not fit dose response: {e}")
                            vmax, km, r_squared = None, None, None
                            dose_response = []
                    else:
                        r_squared, vmax, km, diff_data, response = (
                            None,
                            None,
                            None,
                            None,
                            None,
                        )

                    # for well in test_wells:
                    #     session.refresh(well)

                    well_volume = set(
                        [well.volume for well in test_wells + control_wells]
                    )
                    assert len(well_volume) == 1
                    well_volume = well_volume.pop()

                    protein_concentration = set(
                        [well.protein_concentration for well in test_wells]
                    )
                    assert len(protein_concentration) == 1
                    protein_concentration = protein_concentration.pop()

                    result = model.Result(
                        plate_data_file=plate_data_file,
                        protein=protein,
                        # test_wells=test_wells,
                        # control_wells=control_wells,
                        experiment=experiment,
                        plate=plate,
                        compound=compound,
                        km=km,
                        vmax=vmax,
                        r_squared=r_squared,
                        dose_response=dose_responses,
                        protein_concentration=protein_concentration,
                    )
                    session.add(result)
                    session.commit()
                    session.refresh(result)

                    for well in test_wells:
                        well_result_link_test = model.WellResultLink(
                            well_id=well.id, result_id=result.id, well_type="test"
                        )
                        session.add(well_result_link_test)

                    for well in control_wells:
                        well_result_link_control = model.WellResultLink(
                            well_id=well.id,
                            result_id=result.id,
                            well_type="control",
                        )
                        session.add(well_result_link_control)

                    session.commit()


if __name__ == "__main__":
    main(sys.argv[1:])
