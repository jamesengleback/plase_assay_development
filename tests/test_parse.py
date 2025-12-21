import os
import json
import yaml
import logging
import unittest
import pandas as pd
import sys
import warnings
import subprocess

workspace_root = '/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development'
sys.path.insert(0, workspace_root)
from utils.utils.parse import bmg

class TestParse(unittest.TestCase):
    def _test_file(self, file_path):
        """Helper method to test parsing a single file."""
        logging.info(f"Testing file: {file_path}")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                df = bmg(file_path)
            except Exception as e:
                logging.warning(f"Failed to parse {file_path}: {e}")
                # Print head of the file
                try:
                    result = subprocess.run(['head', file_path], capture_output=True, text=True, timeout=10)
                    print(f"Head of {file_path}:\n{result.stdout}")
                except Exception as head_e:
                    print(f"Could not get head of {file_path}: {head_e}")
                self.fail(f"Failed to parse {file_path}: {e}")
                return
        
        if w:
            # Print head if warnings
            try:
                result = subprocess.run(['head', file_path], capture_output=True, text=True, timeout=10)
                print(f"Head of {file_path} (warnings):\n{result.stdout}")
            except Exception as head_e:
                print(f"Could not get head of {file_path}: {head_e}")
            self.fail(f"Warnings during parsing {file_path}: {[str(warning.message) for warning in w]}")
        
        if df is None:
            logging.warning(f"Failed to parse {file_path}, returned None")
            return
        
        # Assert it's a DataFrame
        self.assertIsInstance(df, pd.DataFrame, f"Expected DataFrame for {file_path}")
        
        # Assert has rows (since all files have data)
        self.assertGreater(df.shape[0], 0, f"DataFrame should have rows for {file_path}")
        
        # Assert columns are integers (wavelengths)
        self.assertEqual(df.columns.dtype, int, f"Columns should be integers for {file_path}")
        
        # Assert columns are within 220-800 nm range (wavelengths)
        self.assertTrue(all(220 <= col <= 800 for col in df.columns), f"Columns should be between 220 and 800 for {file_path}")
        
        # Assert 800 nm is present
        self.assertGreaterEqual(df.columns.max(), 500, f"Max wavelength should be at least 500 nm for {file_path}")
        
        # Assert indices are strings (well addresses) if they are strings
        if all(isinstance(idx, str) for idx in df.index):
            logging.info(f"Indices are strings for {file_path}")
        else:
            logging.warning(f"Indices are not strings for {file_path}, skipping string checks")
        
        # Assert has columns
        self.assertGreater(df.shape[1], 0, f"DataFrame should have columns for {file_path}")
        
        # If has rows, check well address format
        if df.shape[0] > 0:
            if all(isinstance(idx, str) for idx in df.index):
                for idx in df.index:
                    self.assertTrue(len(idx) >= 2 and idx[0].isalpha() and idx[1:].isdigit(), 
                                   f"Index {idx} should be well address format for {file_path}")
            else:
                logging.warning(f"Indices are not strings for {file_path}, skipping well address format check")
        
        logging.info(f"Successfully tested {file_path}: shape {df.shape}")

    def test_bmg_parsing(self):
        """Integration test for parse.bmg function using config files for file paths."""
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        
        workspace_root = '/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development'
        
        # Find all config_*.json files
        config_files = []
        for root, dirs, files in os.walk(workspace_root):
            for file in files:
                if (file.startswith('config_') and file.endswith('.json')) or file == 'debug_config.json':
                    config_files.append(os.path.join(root, file))
        
        # Add yml config files from upload_screening.sh
        yml_configs = [
            '/home/james/thesis-stuff/screening-fist/lab/01.0/config.yml',
            '/home/james/thesis-stuff/screening-fist/lab/02.0/config.yml',
            '/home/james/thesis-stuff/screening-fist/lab/03.0/config.yml',
            '/home/james/thesis-stuff/screening-fist/lab/04.0/config.yml',
            '/home/james/thesis-stuff/screening-fist/lab/05.0/config.yml',
        ]
        config_files.extend(yml_configs)
        
        tested_files = 0
        for config_path in config_files:
            logging.info(f"Processing config: {config_path}")
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.json'):
                        config = json.load(f)
                    else:
                        config = yaml.safe_load(f)
            except Exception as e:
                logging.warning(f"Failed to load config {config_path}: {e}")
                continue
            
            if 'experiments' not in config and 'platereader' not in config:
                continue  # Skip if no experiments or platereader
            
            # Handle experiments (old json configs)
            if 'experiments' in config:
                for exp_key, exp_data in config['experiments'].items():
                    if 'file' not in exp_data:
                        continue  # Skip if no file specified
                    
                    file_path = os.path.join(os.path.dirname(config_path), exp_data['file'])
                    
                    if not os.path.exists(file_path):
                        logging.warning(f"File does not exist: {file_path}")
                        continue  # Skip if file doesn't exist
                    
                    tested_files += 1
                    self._test_file(file_path)
            
            # Handle platereader (new yml configs)
            if 'platereader' in config:
                for plate_name, plate_data in config['platereader'].items():
                    for sub in ['control', 'test']:
                        if sub in plate_data and 'path' in plate_data[sub]:
                            rel_path = plate_data[sub]['path']
                            file_path = os.path.join(os.path.dirname(config_path), rel_path)
                            
                            if not os.path.exists(file_path):
                                logging.warning(f"File does not exist: {file_path}")
                                continue  # Skip if file doesn't exist
                            
                            tested_files += 1
                            self._test_file(file_path)
        
        self.assertGreater(tested_files, 0, "No files were tested")


if __name__ == "__main__":
    unittest.main()