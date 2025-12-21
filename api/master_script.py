#!/usr/bin/env python3
"""
Master script to backup database, recreate it, upload experiments, copy annotations,
upload screening experiments, and apply anomaly detection.
"""

import os
import shutil
import subprocess
import datetime
from sqlalchemy import create_engine
from api import model
import tqdm

def log(message):
    """Log a message with green color to stand out."""
    print(f"\033[92m{message}\033[0m")

# Define config lists based on shell scripts
assay_manual_configs = [
    "../3_TestFattyAcids/config_3.json",
    "../4_MoreIterations/config_4.json",
    "../5_More_Iterations/config_5.json",
    "../6_More_iterationns/config_6.json",
    "../7_Moreiterations/config_7.json",
    "../8_MoIterations/config_8.json",
    "../9_Almost_there/config_9.json",
    "../11_Validation/config_11.json",
    "../12_ThermoPlateCompare/config_12.json",
    "../13_TitrationValidationPilot/config_13.json",
    "../14_DMSO_dilutionScheme/config_14.json",
    "../22_validation2/config_22.json"
]

assay_echo_configs = [
    "../15_Echo/config_15.json",
    "../16_Echo/config_16.json",
    "../17_Buffers/config_17.json",
    "../18_BuffersNCompounds/config_18.json",
    "../19_Validation/config_19.json",
    "../20_SpinShift/config_20.json",
    "../21_SpinShift2/config_21.json"
]

screening_configs = [
    "~/thesis-stuff/screening-fist/lab/01.0/config.yml",
    "~/thesis-stuff/screening-fist/lab/02.0/config.yml",
    "~/thesis-stuff/screening-fist/lab/03.0/config.yml",
    "~/thesis-stuff/screening-fist/lab/04.0/config.yml",
    "~/thesis-stuff/screening-fist/lab/05.0/config.yml"
]

def backup_database():
    """Backup the current database.db to db_checkpoints with timestamp."""
    if not os.path.exists("database.db"):
        log("No database.db found to backup.")
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"./db_checkpoints/{timestamp}-backup.db"
    os.makedirs("./db_checkpoints", exist_ok=True)
    shutil.copy("database.db", backup_path)
    log(f"Backed up database.db to {backup_path}")
    return backup_path

def recreate_database():
    """Delete and recreate the database by creating all tables."""
    if os.path.exists("database.db"):
        os.remove("database.db")
        log("Removed existing database.db")
    
    # Create engine and tables
    engine = create_engine("sqlite:///database.db")
    model.SQLModel.metadata.create_all(engine)
    log("Recreated database.db with all tables")

def upload_assay_development_experiments():
    """Upload assay development experiments."""
    # Upload manual experiments
    if assay_manual_configs:
        log(f"Uploading {len(assay_manual_configs)} manual experiments...")
        for config in tqdm.tqdm(assay_manual_configs, desc="Manual uploads"):
            log(f"Uploading manual config: {config}")
            result = subprocess.run(["python", "scripts/upload_manual.py", config], capture_output=True, text=True)
            if result.returncode == 0:
                log(f"Successfully uploaded {config}")
            else:
                log(f"Failed to upload {config}: {result.stderr}")
    
    # Upload echo experiments
    if assay_echo_configs:
        log(f"Uploading {len(assay_echo_configs)} echo experiments...")
        for config in tqdm.tqdm(assay_echo_configs, desc="Echo uploads"):
            log(f"Uploading echo config: {config}")
            result = subprocess.run(["python", "scripts/upload_echo.py", config], capture_output=True, text=True)
            if result.returncode == 0:
                log(f"Successfully uploaded {config}")
            else:
                log(f"Failed to upload {config}: {result.stderr}")

def copy_annotations(backup_path):
    """Copy annotations from backup."""
    if not backup_path:
        log("No backup path, skipping annotation copy")
        return
    
    log("Copying annotations...")
    result = subprocess.run(["python", "copy_annotations.py", backup_path], capture_output=True, text=True)
    if result.returncode == 0:
        log("Copied annotations successfully")
    else:
        log(f"Failed to copy annotations: {result.stderr}")

def upload_screening_experiments():
    """Upload screening experiments."""
    expanded_configs = [os.path.expanduser(config) for config in screening_configs]
    log(f"Uploading {len(expanded_configs)} screening experiments...")
    for config in tqdm.tqdm(expanded_configs, desc="Screening uploads"):
        log(f"Uploading screening config: {config}")
        result = subprocess.run(["python", "scripts/upload_screening_experiment.py", config], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Successfully uploaded {config}")
        else:
            log(f"Failed to upload {config}: {result.stderr}")

def apply_anomaly_detection():
    """Apply anomaly detection and result exclusion models."""
    log("Applying anomaly detection...")
    result = subprocess.run(["python", "../anomaly_detection/apply_anomaly_detection.py", "--model_path", "../anomaly_detection/best_model.pth"], capture_output=True, text=True)
    if result.returncode == 0:
        log("Applied anomaly detection successfully")
    else:
        log(f"Failed to apply anomaly detection: {result.stderr}")

def main():
    log("Starting master script...")
    
    # 1. Backup database
    log("Backing up database...")
    backup_path = backup_database()
    
    # 2. Recreate database
    log("Recreating database...")
    recreate_database()
    
    # 3. Upload assay development experiments
    log("Uploading assay development experiments...")
    upload_assay_development_experiments()
    
    # 4. Copy annotations
    log("Copying annotations...")
    copy_annotations(backup_path)
    
    # 5. Upload screening experiments
    log("Uploading screening experiments...")
    upload_screening_experiments()
    
    # 6. Apply anomaly detection
    log("Applying anomaly detection...")
    apply_anomaly_detection()
    
    log("Master script completed.")

if __name__ == "__main__":
    main()