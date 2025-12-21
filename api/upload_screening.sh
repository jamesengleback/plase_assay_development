#!/bin/bash
python scripts/upload_screening_experiment.py ~/thesis-stuff/screening-fist/lab/01.0/config.yml \
                    ~/thesis-stuff/screening-fist/lab/02.0/config.yml \
                    ~/thesis-stuff/screening-fist/lab/03.0/config.yml \
                    ~/thesis-stuff/screening-fist/lab/04.0/config.yml \
                    ~/thesis-stuff/screening-fist/lab/05.0/config.yml \
                    --smiles ~/thesis-stuff/screening-fist/ids-smiles-names.json

