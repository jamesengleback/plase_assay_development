import os
import json
import sys
import re
import yaml
import argparse
import datetime
from pprint import pprint
import logging

from sqlmodel import SQLModel, Session, select
from api import model
import utils

import pandas as pd


logging.basicConfig(level=logging.INFO)


def main(args):
    # with Session(model.engine) as session:
    smiles_config = None
    if args.smiles:
        with open(args.smiles, 'r') as f:
            smiles_config = json.load(f)

    for path in args.config:
        config_root_path = os.path.dirname(path)
        with open(path) as f:
            config = yaml.full_load(f)
        picklist_paths_relative = config['echo']['picklist']
        assert len(picklist_paths_relative) == 1
        picklist_path_relative = picklist_paths_relative[0]
        picklist_path = os.path.join(config_root_path, picklist_path_relative)
        assert os.path.exists(picklist_path)
        picklist_df = pd.read_csv(picklist_path, index_col=None)
        # print(df)
        # print(smiles_config)

        PROTEIN_NAME = config['protein']
        # protein = model.Protein(
        #     name=PROTEIN_NAME,
        #     sequence='',
        #     purification="ni",
        # )  # get or create
        # session.add(protein)
        # session.commit()
        # session.refresh(protein)

        plate_dates = []
        for plate_info in config['platereader'].values():
            for plate in plate_info.values():
                measurement_date = datetime.datetime.strptime(plate['date'], '%d/%m/%Y')
                plate_dates.append(measurement_date)
        experiment_start_date = min(plate_dates)

        # experiment = model.Experiment(
        #     id=experiment_number,
        #     start_date=experiment_start_date,
        #     dispense_ligands="echo",
        #     dispense_assay_mix="electronic_multichannel_pipette",
        #     # centrifuge_minutes=0,
        #     # centrifuge_rpm=0,
        #     # protein_days_thawed=constants.get("protein_days_thawed"),
        # )
        # SQLModel.model_validate(experiment)
        # session.add(experiment)

        for plate_name, plate_info in zip(config['platereader'].keys(),
                                          config['platereader'].values()):

            plate_number = re.search('([0-9]+)', plate_name).group(0)
            test_plate_info = plate_info['test']
            test_plate_path = os.path.join(config_root_path, test_plate_info['path'])
            assert os.path.exists(test_plate_path)
            test_plate_df = utils.parse.bmg(test_plate_path)

            control_plate_info = plate_info['control']
            control_plate_path = os.path.join(config_root_path, control_plate_info['path'])
            assert os.path.exists(control_plate_path)
            control_plate_df = utils.parse.bmg(control_plate_path)
            # control_plate = plate_info['control']
            # pprint(plate_name)
            # pprint(plate_info)
            #
            # test_plate = model.Plate(
            #     label=plate_name,
            #     experiment=experiment,
            #     # product_name=experiment_config.get("plate_type"),
            # )
            #
            # session.add(test_plate)
            # session.commit()
            # session.refresh(test_plate)
            # experiment.plates.append(test_plate)
            #
            # plate_data_file = model.PlateDataFile(
            #     path=test_plate_path,
            #     # hash=file_hash(plate_data_path),
            #     parse_error=False,
            # )
            #
            # try:
            #     session.add(plate_data_file)
            #     session.commit()
            #     session.refresh(plate_data_file)
            # except Exception as e:
            #     logging.warning(e)
            #
            import ipdb ; ipdb.set_trace()
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', nargs='+')
    parser.add_argument('-s', '--smiles')
    args = parser.parse_args()
    main(args)
