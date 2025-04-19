import sys
import os
import json
import logging
import datetime
import hashlib
from string import ascii_uppercase
import colorama
from sqlmodel import SQLModel, Session, select
import numpy as np
import utils
from utils.plot import plot_group
from api import model

logging.basicConfig(level=logging.WARNING)

COMPOUNDS = {
        'Arachadionic acid': {
            'smiles': r'CCCCC/C=C\C/C=C\C/C=C\C/C=C\CCCC(=O)O',
            'mw': 304.5,
            }

        }

PROTEIN_NAME = 'BM3 WT'

class TextStyle:
    def bgreen(s):
        return f'{colorama.Style.BRIGHT + colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}'
    def green(s):
        return f'{colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}'
    def bred(s):
        return f'{colorama.Style.BRIGHT + colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}'
    def red(s):
        return f'{colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}'


def main(args):
    import ipdb ; ipdb.set_trace()
    with Session(model.engine) as session:
        protein = session.exec(select(model.Protein).where(model.Protein.name == PROTEIN_NAME)).first()
        if protein is None:
            protein = model.Protein(name=PROTEIN_NAME) # get or create 
        for arg in args:
            path = os.path.abspath(arg)
            logging.info(path)
            assert os.path.exists(path), os.path.isfile(path)
            working_directory = os.path.abspath(os.path.dirname(arg))

            with open(path, 'r') as f:
                config_data = json.load(f)

            constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                              config_data.values(),
                                              ) if not isinstance(j, (list, dict))
                         }
            experiment = model.Experiment(
                    start_date=datetime.date(2018, 8, 19),
                    dispense_ligands='echo',
                    dispense_assay_mix='peristaltic_pump',
                    centrifuge_minutes=config_data.get('centrifuge_minutes'),
                    centrifuge_rpm=config_data.get('centrifuge_rpm'),
                    protein_days_thawed=None, # in plate config items
                    )

            SQLModel.model_validate(experiment)
            session.add(experiment)
            # session.commit()
            # session.refresh(experiment)

            plate_config = config_data.get('experiments')
            for plate_config_key, plate_config_value in plate_config.items():
                file_path = os.path.join(working_directory, plate_config_value['file'])
                assert os.path.exists(file_path)
                experiment.protein_days_thawed = plate_config_value.get('protein_days_thawed')
                # experiment.protein_concentration = plate_config_value.get('protein_concentration')

                df = utils.parse.bmg(file_path)
                plate_file = model.PlateDataFile(path=file_path,
                                                 hash=file_hash(file_path),
                                                 parse_error=False,
                                                 )

                try:
                    session.add(plate_file)
                    session.commit()
                    session.refresh(plate_file)
                except Exception as e:
                    logging.warning(e)
                    # continue


                plate = model.Plate(label=plate_config_key,
                                    experiment=experiment,
                                    product_name=plate_config_value.get('plate_type'),
                        )

                session.add(plate)
                session.commit()
                session.refresh(plate)
                experiment.plates.append(plate)

                blocks = config_data['blocks']
                for block_num, block in zip(blocks.keys(), blocks.values()):
                    independent_variables = constants | {i: block[i] for i in block if isinstance(block[i], (str, int, float))}
                    compound_name = independent_variables['ligand']

                    compound = session.exec(select(model.Compound).where(model.Compound.name==compound_name)).first()
                    if compound is None:
                        compound = model.Compound(name=compound_name,
                                                  canonical_smiles=COMPOUNDS[compound_name]['smiles'],
                                                  mw=COMPOUNDS[compound_name]['mw'],
                                                  )

                    test_wells = []
                    control_wells = []
                    for conc, test_well_addr, control_well_addr in zip(block['concentrations'],
                                                                       block['test_wells'],
                                                                       block['control_wells'],
                                                                       ):
                        test_wells = []
                        control_wells = []
                        for well_addr, well_list in zip([test_well_addr, control_well_addr],
                                                        [test_wells, control_wells]):

                            well = model.Well(
                                    plate_id=plate.id,
                                    plate=plate,
                                    compound_id=compound.id,
                                    compound=compound,
                                    protein=protein,
                                    protein_id=protein.id,
                                    file=plate_file,
                                    file_id=plate_file.id,
                                    protein_concentration=5,
                                    compound_concentration=conc,
                                    address=well_addr,
                                    total_volume=independent_variables.get('well_volume'),
                                    )
                            session.add(well)
                            session.commit()
                            session.refresh(well)
                            well_list.append(well)

                            well_absorbance = df.loc[well_addr, :]

                            absorbance_items = []
                            for wavelength, absorbance_value in zip(well_absorbance.index, well_absorbance.values):
                                absorbance = model.Absorbance(
                                        wavelength=wavelength,
                                        absorbance=absorbance_value,
                                        well_id=well.id,
                                        plate_data_file_id=plate_file.id
                                        )
                                absorbance_items.append(absorbance)
                            session.add_all(absorbance_items)
                            session.commit()

                    concs = np.array(block['concentrations'])
                    test_data = df.loc[list(block['test_wells']), :]

                    control_wells = block.get('control_wells')
                    if control_wells:
                        control_data = df.loc[list(control_wells), :]
                        if control_data.isna().all().all():
                            control_data = control_data.fillna(0)
                    else:
                        control_data = None

                    if control_wells:
                        corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))
                    else:
                        corrected_data = test_data

                    corrected_data = corrected_data.subtract(corrected_data[800], axis=0)

                    if concs is not None:
                        corrected_data = corrected_data.sort_index()
                        diff_data = corrected_data.subtract(corrected_data.iloc[concs.argmin(), :], axis=1)
                        response = utils.mm.calculate_response(diff_data)

                        try:
                            vmax, km = utils.mm.calculate_km(response, response.index)
                            rsq = utils.mm.r_squared(response, utils.mm.curve(concs, vmax, km))
                        except:
                            vmax, km, rsq = None, None, None
                    else:
                        rsq, vmax, km, diff_data, response = None, None, None, None, None

                    result = model.Result(test_wells=test_wells,
                                          experiment=experiment,
                                          experiment_id=experiment.id,
                                          plate_id=plate.id,
                                          plate=plate,
                                          compound=compound,
                                          compound_id=compound.id,
                                          km=km,
                                          vmax=vmax,
                                          rsq=rsq,
                                          )
                    session.add(result)
                    session.commit()


def file_hash(path: str) -> str:
    assert os.path.exists(path)
    assert os.path.isfile(path)
    hash = hashlib.md5()
    buffer = bytearray(128*1024)
    mv = memoryview(buffer)
    with open(path, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            hash.update(mv[:n])
    return hash.hexdigest()

if __name__ == '__main__':
    # SQLModel.metadata.create_all(model.engine)
    main(sys.argv[1:])
