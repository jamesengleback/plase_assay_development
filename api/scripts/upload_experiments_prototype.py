import sys
import os
import re
import json
import logging
import datetime
import hashlib
from string import ascii_uppercase
import colorama
from sqlmodel import SQLModel, Session, select
import numpy as np
from rdkit import Chem
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdDepictor
from rdkit.Chem import Descriptors
from rdkit.Chem import AllChem
import utils
from utils.plot import plot_group
from api import model


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


def moltosvg(mol, molSize=(450, 150), kekulize=True):
    """from https://rdkit.blogspot.com/2015/02/new-drawing-code.html"""
    mc = Chem.Mol(mol.ToBinary())
    if kekulize:
        try:
            Chem.Kekulize(mc)
        except:
            mc = Chem.Mol(mol.ToBinary())
    if not mc.GetNumConformers():
        rdDepictor.Compute2DCoords(mc)
    drawer = rdMolDraw2D.MolDraw2DSVG(molSize[0], molSize[1])
    drawer.DrawMolecule(mc)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    # It seems that the svg renderer used doesn't quite hit the spec.
    # Here are some fixes to make it work in the notebook, although I think
    # the underlying issue needs to be resolved at the generation step
    return svg.replace("svg:", "")


def smiles_to_dict(smiles):
    mol = Chem.MolFromSmiles(smiles)
    svg = moltosvg(mol)
    mol = Chem.AddHs(mol)
    mw = Descriptors.MolWt(mol)
    return {"mw": mw, "svg": svg}


COMPOUNDS = {
    i: {**COMPOUNDS[i], **smiles_to_dict(COMPOUNDS[i]["smiles"])}
    for i in COMPOUNDS.keys()
}


PROTEIN_NAME = "BM3 WT"


class TextStyle:
    def bgreen(s):
        return f"{colorama.Style.BRIGHT + colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}"

    def green(s):
        return f"{colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}"

    def bred(s):
        return (
            f"{colorama.Style.BRIGHT + colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}"
        )

    def red(s):
        return f"{colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}"


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

        for arg in args:
            path = os.path.abspath(arg)
            if experiment_number := re.search(
                "[0-9]+", os.path.basename(os.path.dirname(path))
            ):
                experiment_number = int(experiment_number.group())
                logging.info(f"experiment_number: {experiment_number}")
            else:
                raise Warning(f"experiment_number not found in {path}")
            logging.info(path)
            assert os.path.exists(path), os.path.isfile(path)
            working_directory = os.path.abspath(os.path.dirname(arg))

            with open(path, "r") as f:
                config_data = json.load(f)

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
                experiment = model.Experiment(
                    id=experiment_number,
                    start_date=datetime.date(2018, 8, 19),
                    dispense_ligands="echo",
                    dispense_assay_mix="peristaltic_pump",
                    centrifuge_minutes=config_data.get("centrifuge_minutes"),
                    centrifuge_rpm=config_data.get("centrifuge_rpm"),
                    protein_days_thawed=None,  # in plate config items
                )

            SQLModel.model_validate(experiment)
            session.add(experiment)
            # session.commit()
            # session.refresh(experiment)

            plate_config = config_data.get("experiments")
            for plate_config_key, plate_config_value in plate_config.items():
                file_path = os.path.join(working_directory, plate_config_value["file"])
                assert os.path.exists(file_path)
                experiment.protein_days_thawed = plate_config_value.get(
                    "protein_days_thawed"
                )
                # experiment.protein_concentration = plate_config_value.get('protein_concentration')

                df = utils.parse.bmg(file_path)

                assert df is not None

                plate_data_file = model.PlateDataFile(
                    path=file_path,
                    hash=file_hash(file_path),
                    parse_error=False,
                )

                try:
                    session.add(plate_data_file)
                    session.commit()
                    session.refresh(plate_data_file)
                except Exception as e:
                    logging.warning(e)
                    # continue

                plate = model.Plate(
                    label=plate_config_key,
                    experiment=experiment,
                    product_name=plate_config_value.get("plate_type"),
                )

                session.add(plate)
                session.commit()
                session.refresh(plate)
                experiment.plates.append(plate)

                if blocks := config_data.get("blocks"):
                    for block_num, block in zip(blocks.keys(), blocks.values()):
                        independent_variables = (
                            constants
                            | plate_config
                            | {
                                i: block[i]
                                for i in block
                                if isinstance(block[i], (str, int, float))
                            }
                            | plate_config_value
                        )
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
                        control_wells = []
                        for conc, test_well_addr, control_well_addr in zip(
                            block.get("concentrations"),
                            block.get("test_wells"),
                            block.get("control_wells"),
                        ):
                            # test wells
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

                            # control wells
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

                        concs = np.array(block["concentrations"])
                        test_data = df.loc[list(block["test_wells"]), :]

                        control_wells_addr = block["control_wells"]
                        if control_wells_addr:
                            control_data = df.loc[list(control_wells_addr), :]
                            if control_data.isna().all().all():
                                control_data = control_data.fillna(0)
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
                                for conc_i, response_i, test_well, control_well in zip(
                                    concs, response, test_wells, control_wells
                                ):
                                    test_well = session.refresh(test_well)
                                    control_well = session.refresh(control_well)
                                    dose_response = model.DoseResponse(
                                        concentration=conc_i,
                                        response=response_i,
                                        test_well=test_well,
                                        conrol_well=control_well,
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


if __name__ == "__main__":
    # SQLModel.metadata.create_all(model.engine)
    main(sys.argv[1:])
