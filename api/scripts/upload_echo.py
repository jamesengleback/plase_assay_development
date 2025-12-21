import sys
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

logging.basicConfig(level=logging.INFO)

PROTEINS = {
    "BM3 WT": {
        "sequence": "MTIKEMPQPKTFGELKNLPLLNTDKPVQALMKIADELGEIFKFEAPGRVTRYLSSQRLIKEACDESRFDKNLSQALKFVRDFAGDGLFTSWTHEKNWKKAHNILLPSFSQQAMKGYHAMMVDIAVQLVQKWERLNADEHIEVPEDMTRLTLDTIGLCGFNYRFNSFYRDQPHPFITSMVRALDEAMNKLQRANPDDPAYDENKRQFQEDIKVMNDLVDKIIADRKASGEQSDDLLTHMLNGKDPETGEPLDDENIRYQIITFLIAGHETTSGLLSFALYFLVKNPHVLQKAAEEAARVLVDPVPSYKQVKQLKYVGMVLNEALRLWPTAPAFSLYAKEDTVLGGEYPLEKGDELMVLIPQLHRDKTIWGDDVEEFRPERFENPSAIPQHAFKPFGNGQRACIGQQFALHEATLVLGMMLKHFDFEDHTNYELDIKETLTLKPEGFVVKAKSKKIPLGGIPSPSTEQSAKKVRK*"
    }
}


COMPOUNDS = {
    "arachadionic acid": {
        "smiles": r"CCCCC/C=C\C/C=C\C/C=C\C/C=C\CCCC(=O)O",
        "mw": None,
        "svg": None,
    },
    "dmso": {
        "smiles": r"CS(=O)C",
        "mw": 78.14,
        "svg": None,
    },
    "lauric acid": {
        "smiles": r"CCCCCCCCCCCC(=O)O",
        "mw": None,
        "svg": None,
    },
    "palmitic acid": {"smiles": r"CCCCCCCCCCCCCCCC(=O)O", "mw": None, "svg": None},
    "4-phenylimidazole": {"smiles": r"C1=CC=C(C=C1)C2=CN=CN2", "mw": None, "svg": None},
}

well_ids = {
    i: j
    for i, j in enumerate(
        [f"{k}{l}" for k in ascii_uppercase[:16] for l in range(1, 25)], 1
    )
}

PROTEIN_NAME = "BM3 WT"


def file_hash(path: str) -> str:
    assert os.path.exists(path)
    assert os.path.isfile(path)
    hash = hashlib.md5()
    buffer = bytearray(128 * 1024)
    mv = memoryview(buffer)
    with open(path, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            hash.update(mv[:n])
    return hash.hexdigest()


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
                        dispense_bulk = 'electronic_multichannel_pipette'
                    elif dispense_bulk.lower() == "thermo multidrop combi":
                        dispense_bulk = 'peristaltic_pump'
                dispense_ligands = constants.get("dispense_ligands")
                if dispense_ligands is not None:
                    if dispense_ligands.lower() == "serial dilution":
                        dispense_ligands = 'serial_dilution'
                if dispense_ligands is not None:
                    dispense_ligands = dispense_ligands.lower()
                experiment = model.Experiment(
                    id=experiment_number,
                    start_date=datetime.date.fromisoformat(constants.get("start_date")),
                    dispense_ligands=dispense_ligands,
                    dispense_assay_mix=dispense_bulk,
                    centrifuge_minutes=constants.get("centrifuge_minutes"),
                    centrifuge_rpm=constants.get("centrifuge_rpm"),
                    protein_days_thawed=constants.get("protein_days_thawed"),
                )

            SQLModel.model_validate(experiment)
            session.add(experiment)

            experiments = config_data.get("experiments")
            blocks = config_data.get("blocks")
            for experiment_name in experiments.keys():
                experiment_config = experiments[experiment_name]

                if blocks is None:
                    blocks = experiment_config.get("blocks")

                if (plate_data_path := experiment_config.get("file")) is not None:
                    plate_data_path = os.path.join(working_directory, plate_data_path)
                    logging.info(plate_data_path)

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

                    plate = model.Plate(
                        label=experiment_name,
                        experiment=experiment,
                        product_name=experiment_config.get("plate_type"),
                    )

                    session.add(plate)
                    session.commit()
                    session.refresh(plate)
                    experiment.plates.append(plate)

                    df = utils.parse.bmg(plate_data_path)
                    for block_num, block in zip(blocks.keys(), blocks.values()):
                        independent_variables = constants | {
                            i: block[i]
                            for i in block
                            if isinstance(block[i], (str, int, float))
                        } | experiment_config
                        ligand = (
                            block.get("ligand")
                            or experiment_config.get("ligand")
                            or config_data.get("ligand")
                        )
                        logging.info(
                            f"{experiment_number} {independent_variables.get('dispense_ligands')}  block {block_num} ligand {ligand}"
                        )

                        concs = (
                            block.get("concentrations")
                            or experiment_config.get("concentrations")
                            or config_data.get("concentrations")
                        )
                        if concs is not None:
                            concs = np.array(concs)
                        else:
                            concs = np.array([0] * len(block["test_wells"]))  # all zero

                        compound_name = independent_variables.get("ligand", "")
                        compound = session.exec(
                            select(model.Compound).where(
                                model.Compound.name == compound_name
                            )
                        ).first()
                        if compound is None:
                            compound_item = COMPOUNDS.get(compound_name.lower(), {})
                            compound = model.Compound(
                                name=compound_name,
                                canonical_smiles=compound_item.get("smiles"),
                                mw=compound_item.get("mw"),
                                svg=compound_item.get("svg"),
                            )

                        test_wells = []
                        for conc, test_well_addr in zip(
                            concs,
                            block.get("test_wells", []),
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

                            try:
                                well_absorbance = df.loc[test_well_addr, :]
                            except KeyError as e:
                                logging.error(f"Well {test_well_addr} nmy_ot found in CSV. Available wells: {df.index.tolist()[:10]}...")
                                continue  # Skip this well

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
                        for conc, control_well_addr in zip(
                            concs,
                            block.get("control_wells", []),
                        ):
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

                            try:
                                well_absorbance = df.loc[control_well_addr, :]
                            except KeyError as e:
                                logging.error(f"Well {control_well_addr} not found in CSV. Available wells: {df.index.tolist()[:10]}...")
                                continue  # Skip this well

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

                        try:
                            test_data = df.loc[list(block["test_wells"]), :]
                        except KeyError as e:
                            logging.error(f"Test wells {block['test_wells']} not found in CSV. Available wells: {df.index.tolist()[:10]}...")
                            test_data = None  # or handle appropriately

                        control_wells_addr = block.get("control_wells")
                        if control_wells_addr:
                            try:
                                control_data = df.loc[list(control_wells_addr), :]
                                if control_data.isna().all().all():
                                    control_data = control_data.fillna(0)
                            except KeyError as e:
                                logging.error(f"Control wells {control_wells_addr} not found in CSV. Available wells: {df.index.tolist()[:10]}...")
                                control_data = None
                        else:
                            control_data = None

                        if control_wells_addr:
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
