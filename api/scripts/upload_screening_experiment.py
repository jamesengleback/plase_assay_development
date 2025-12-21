import os
import json
import sys
import re
import yaml
import argparse
import datetime
from string import ascii_uppercase
from pprint import pprint
import logging

import numpy as np
from sqlmodel import SQLModel, Session, select
from api import model
import utils

import pandas as pd


logging.basicConfig(level=logging.INFO)

PARAMS = {
    "well_volume": 30,
    "stock_compound_concentration": 10,
}

POSSIBLE_WELL_ADDRESSES = [
    f"{i}{j}" for i in ascii_uppercase[:16] for j in range(1, 25)
]


def main(args):
    with Session(model.engine) as session:
        smiles_config = None
        if args.smiles:
            with open(args.smiles, "r") as f:
                smiles_config = json.load(f)

        for path in args.config:
            experiment_directory_name = os.path.basename(os.path.dirname(path))
            experiment_number_search = re.search("[0-9]+", experiment_directory_name)
            if experiment_number_search:
                experiment_number = int(experiment_number_search.group()) + 100
            else:
                raise Warning(f"experiment_number not found in {path}")
            config_root_path = os.path.dirname(path)
            with open(path) as f:
                config = yaml.full_load(f)

            echo_reports = [i for i in config["echo"]["transfers"] if "Exception" in i]
            assert len(echo_reports) == 1
            echo_transfer_df = pd.read_csv(
                os.path.join(config_root_path, echo_reports[0]), index_col=None
            )

            echo_transfer_df["dest_plate"] = echo_transfer_df[
                "Destination Plate Name"
            ].apply(lambda x: f"plate_{int(re.search('[0-9]+', x).group()) - 1}")

            picklist_paths_relative = config["echo"]["picklist"]
            assert len(picklist_paths_relative) == 1
            picklist_path_relative = picklist_paths_relative[0]
            picklist_path = os.path.join(config_root_path, picklist_path_relative)
            assert os.path.exists(picklist_path)
            picklist_df = pd.read_csv(picklist_path, index_col=None)

            plate_name_map = dict(
                zip(
                    picklist_df["Destination Plate Name"].unique(),
                    [f"plate_{i}" for i in range(1, 16)],
                )
            )

            # source_rack_map = {
            #     "src racks 0..4": "Source[2]",
            #     "src racks 4..8": "Source[3]",
            #     "src racks 8..12": "Source[4]",
            # }

            picklist_df["dest_plate"] = picklist_df["Destination Plate Name"].apply(
                lambda i: plate_name_map[i]
            )

            PROTEIN_NAME = config["protein"]["name"]
            protein = model.Protein(
                name=PROTEIN_NAME,
                sequence="",
                purification="ni",
            )  # get or create
            session.add(protein)
            session.commit()
            session.refresh(protein)

            # PROTEIN_CONCENTRATION = config["protein"].get("concentration")
            PROTEIN_CONCENTRATION = None

            if PROTEIN_CONCENTRATION is None:
                try:
                    post_dilution_spec_path_ = config["uv-vis"]["post-dilution spec"][0]
                    post_dilution_spec_path = os.path.join(
                        config_root_path, post_dilution_spec_path_
                    )
                    assert os.path.exists(post_dilution_spec_path)
                    uv_vis = utils.parse.varian(post_dilution_spec_path)
                except Exception as e:
                    pre_dilution_spec_path_ = config["uv-vis"]["pre-dilution spec"][0]
                    pre_dilution_spec_path = os.path.join(
                        config_root_path, pre_dilution_spec_path_
                    )
                    assert os.path.exists(pre_dilution_spec_path)
                    uv_vis = utils.parse.varian(pre_dilution_spec_path)

                uv_vis_corrected = uv_vis.subtract(uv_vis.loc[800, :], axis=1)
                last_col_name = uv_vis_corrected.columns[-1]
                PROTEIN_CONCENTRATION = round(
                    1000 * uv_vis_corrected.loc[420, last_col_name] / 95, 3
                )

            plate_dates = []
            for plate_info in config["platereader"].values():
                for plate in plate_info.values():
                    measurement_date = datetime.datetime.strptime(
                        plate["date"], "%d/%m/%Y"
                    )
                    plate_dates.append(measurement_date)
            experiment_start_date = min(plate_dates)

            experiment = session.exec(
                select(model.Experiment).where(model.Experiment.id == experiment_number)
            ).first()

            if experiment is None:
                experiment = model.Experiment(
                    id=experiment_number,
                    start_date=experiment_start_date,
                    dispense_ligands="echo",
                    dispense_assay_mix="electronic_multichannel_pipette",
                    # centrifuge_minutes=0,
                    # centrifuge_rpm=0,
                    # protein_days_thawed=constants.get("protein_days_thawed"),
                )
                SQLModel.model_validate(experiment)
            session.add(experiment)

            for plate_name, plate_info in zip(
                config["platereader"].keys(), config["platereader"].values()
            ):
                plate_number = re.search("([0-9]+)", plate_name).group(0)
                test_plate_info = plate_info["test"]
                test_plate_path = os.path.join(
                    config_root_path, test_plate_info["path"]
                )
                assert os.path.exists(test_plate_path)
                test_plate_df = utils.parse.bmg(test_plate_path)

                control_plate_info = plate_info["control"]
                control_plate_path = os.path.join(
                    config_root_path, control_plate_info["path"]
                )
                assert os.path.exists(control_plate_path)
                control_plate_df = utils.parse.bmg(control_plate_path)

                picklist_plate_df = picklist_df.query(f'dest_plate == "{plate_name}"')

                echo_transfer_plate_df = echo_transfer_df.query(
                    f'dest_plate == "{plate_name}"'
                )
                echo_transfer_wells = {
                    row["Destination Well"]: row["Actual Volume"]
                    for _, row in echo_transfer_plate_df.iterrows()
                }

                # control_plate = plate_info['control']
                # pprint(plate_name)
                # pprint(plate_info)
                #
                test_plate = session.exec(
                    select(model.Plate).where(
                        model.Plate.experiment == experiment,
                        model.Plate.label == plate_name,
                    )
                ).first()
                if test_plate is None:
                    test_plate = model.Plate(
                        label=plate_name,
                        experiment=experiment,
                        # product_name=experiment_config.get("plate_type"),
                    )
                session.add(test_plate)
                session.commit()
                session.refresh(test_plate)
                experiment.plates.append(test_plate)
                #
                test_plate_data_file = model.PlateDataFile(
                    path=test_plate_path,
                    # hash=file_hash(plate_data_path),
                    parse_error=False,
                )

                try:
                    session.add(test_plate_data_file)
                    session.commit()
                    session.refresh(test_plate_data_file)
                except Exception as e:
                    logging.warning(e)

                # echo
                # echo_reports = config["echo"]["transfers"]
                # echo_transfer_df = pd.read_csv(os.path.join(config_root_path, con))
                for (
                    compound_ID,
                    picklist_plate_compound_chunk_df,
                ) in picklist_plate_df.groupby("Cpd"):
                    smiles = None
                    compound_name = None
                    if smiles_config:
                        item = smiles_config.get(compound_ID)
                        if item:
                            smiles = item["smiles"]
                            compound_name = item["name"]

                    # compound = None
                    compound = session.exec(
                        select(model.Compound).where(
                            model.Compound.name == (compound_name or compound_ID)
                        )
                    ).first()

                    if compound is None:
                        if compound_ID:
                            compound = model.Compound(
                                name=compound_name if compound_name else compound_ID,
                                canonical_smiles=smiles,
                                mw=None,
                                svg=None,
                            )

                    well_addresses = picklist_plate_compound_chunk_df[
                        "DestWell"
                    ].to_list()
                    transfer_volumes = dict(
                        zip(
                            well_addresses,
                            picklist_plate_compound_chunk_df[
                                "Transfer Volume /nl"
                            ].to_list(),
                        )
                    )
                    for well_addr in transfer_volumes.keys():
                        if well_addr in echo_transfer_wells:
                            transfer_volumes[well_addr] = echo_transfer_wells[well_addr]
                    concs = [
                        i
                        * PARAMS["stock_compound_concentration"]
                        / PARAMS["well_volume"]
                        for i in transfer_volumes.values()
                    ]

                    zero_conc_well_address = POSSIBLE_WELL_ADDRESSES[
                        max([POSSIBLE_WELL_ADDRESSES.index(i) for i in well_addresses])
                        + 1
                    ]
                    well_addresses.append(zero_conc_well_address)
                    concs.append(0)
                    concs = np.array(concs)
                    control_wells_data = control_plate_df.loc[well_addresses, :].fillna(
                        0
                    )
                    test_wells_data = test_plate_df.loc[well_addresses, :].fillna(0)

                    test_wells = []
                    for conc, test_well_addr in zip(
                        concs,
                        test_wells_data.index,
                    ):
                        test_well = model.Well(
                            plate=test_plate,
                            compound=compound,
                            protein=protein,
                            plate_data_file=test_plate_data_file,
                            protein_concentration=PROTEIN_CONCENTRATION,
                            compound_concentration=conc,
                            address=test_well_addr,
                            # volume=independent_variables.get("well_volume"),
                        )

                        session.add(test_well)
                        session.commit()
                        session.refresh(test_well)
                        test_wells.append(test_well)

                        test_well_data = test_wells_data.loc[test_well_addr, :]
                        for wavelength, absorbance_value in zip(
                            test_well_data.index, test_well_data.values
                        ):
                            absorbance = model.Absorbance(
                                wavelength=wavelength,
                                absorbance=absorbance_value,
                                well_id=test_well.id,
                                plate_data_file_id=test_plate_data_file.id,
                            )
                            session.add(absorbance)
                        session.commit()

                    control_plate = session.exec(
                        select(model.Plate).where(
                            model.Plate.experiment == experiment,
                            model.Plate.label == plate_name,
                        )
                    ).first()
                    if control_plate is None:
                        control_plate = model.Plate(
                            label=plate_name,
                            experiment=experiment,
                            # product_name=experiment_config.get("plate_type"),
                        )

                    control_plate_data_file = model.PlateDataFile(
                        path=control_plate_path,
                        # hash=file_hash(plate_data_path),
                        parse_error=False,
                    )
                    try:
                        session.add(control_plate_data_file)
                        session.commit()
                        session.refresh(control_plate_data_file)
                    except Exception as e:
                        logging.warning(e)

                    control_wells = []
                    for conc, control_well_addr in zip(concs, control_wells_data.index):
                        control_well = model.Well(
                            plate=control_plate,
                            compound=compound,
                            protein=protein,
                            plate_data_file=control_plate_data_file,
                            protein_concentration=0,
                            compound_concentration=conc,
                            address=control_well_addr,
                            # volume=independent_variables.get("well_volume"),
                        )

                        session.add(control_well)
                        session.commit()
                        session.refresh(control_well)
                        control_wells.append(control_well)

                        control_well_data = control_wells_data.loc[control_well_addr, :]

                        for wavelength, absorbance_value in zip(
                            control_well_data.index, control_well_data.values
                        ):
                            absorbance = model.Absorbance(
                                wavelength=wavelength,
                                absorbance=absorbance_value,
                                well_id=control_well.id,
                                plate_data_file_id=control_plate_data_file.id,
                            )
                            session.add(absorbance)
                        session.commit()
                    if control_well_addr:
                        corrected_data = test_wells_data.reset_index(
                            drop=True
                        ).subtract(control_wells_data.reset_index(drop=True))
                    else:
                        corrected_data = test_wells_data

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
                            a420_max_control = corrected_data.loc[concs.argmin(), 420]
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
                        except:
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
                        plate_data_file=test_plate_data_file,
                        protein=protein,
                        # test_wells=test_wells,
                        # control_wells=control_wells,
                        experiment=experiment,
                        plate=test_plate,
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
                    session.refresh(result)
                    logging.info(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="+")
    parser.add_argument("-s", "--smiles")
    args = parser.parse_args()
    main(args)
