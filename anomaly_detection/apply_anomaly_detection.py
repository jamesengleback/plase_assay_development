import os
import sqlite3
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sqlmodel import Session, select
import sys
sys.path.append('../api')
sys.path.append('../api/api')
import model as db_model
import utils
import logging
import argparse

from sqlmodel import create_engine

# Use the same database as anomaly_detection_script.py
checkpoint_db_path = '../api/database.db'
checkpoint_engine = create_engine(f"sqlite:///{checkpoint_db_path}", echo=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the CNN model (same as in anomaly_detection_script.py)
class CNNAnomalyDetector(nn.Module):
    def __init__(self, input_channels=2, num_classes=1, dropout=0.5):
        super(CNNAnomalyDetector, self).__init__()
        self.conv1 = nn.Conv1d(input_channels, 32, kernel_size=5, stride=1, padding=2)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, stride=1, padding=2)
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = self.pool(x)
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = torch.relu(self.conv3(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.fc(x)
        return x

def load_model(model_path, dropout=0.5):
    model = CNNAnomalyDetector(dropout=dropout)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

def prepare_trace(spectra, diff_spec):
    combined_spec = np.stack([spectra, diff_spec])
    return torch.tensor(combined_spec, dtype=torch.float32).unsqueeze(0)

def main(args):
    # Load model
    model = load_model(args.model_path, args.dropout)
    logger.info(f"Model loaded from {args.model_path}")

    # Connect to database
    with Session(checkpoint_engine) as session:
        # Get all results
        results = session.exec(select(db_model.Result)).all()
        logger.info(f"Found {len(results)} results to process")

        total_excluded = 0
        total_results_processed = 0

        for result in results:
            logger.info(f"Processing result {result.id}")

            # Get dose responses
            dose_responses = session.exec(select(db_model.DoseResponse).where(db_model.DoseResponse.result_id == result.id)).all()

            # First, check for anomalies and exclude
            for dr in dose_responses:
                if dr.exclude:
                    continue

                # Get test and control wells
                test_well = dr.test_well
                control_well = dr.control_well

                if not test_well or not control_well:
                    continue

                # Get absorbance data
                test_abs = {a.wavelength: a.absorbance for a in test_well.absorbance}
                control_abs = {a.wavelength: a.absorbance for a in control_well.absorbance}

                if not test_abs or not control_abs:
                    continue

                # Prepare spectra (300-800)
                wavelengths = sorted([w for w in test_abs.keys() if 300 <= w <= 800])
                test_spec = np.array([test_abs[w] for w in wavelengths])
                control_spec = np.array([control_abs[w] for w in wavelengths])

                # Normalize (subtract 800)
                test_spec -= test_spec[-1] if len(test_spec) > 0 else 0
                control_spec -= control_spec[-1] if len(control_spec) > 0 else 0

                diff_spec = test_spec - control_spec

                logger.info(f"Running anomaly detection for dose response {dr.id}")  # Debug log

                # Run anomaly detection
                trace_tensor = prepare_trace(test_spec, diff_spec)
                with torch.no_grad():
                    output = model(trace_tensor)
                    prob = torch.sigmoid(output).item()
                    pred = prob > args.threshold  # Use configurable threshold

                logger.info(f"Dose response {dr.id}: prob={prob:.4f}, pred={pred}")  # Debug log

                if pred:
                    logger.info(f"Anomaly detected for dose response {dr.id}, excluding")
                    dr.exclude = True
                    session.add(dr)

            session.commit()  # Commit exclusions

            # Now collect data for recalculation
            concs = []
            responses = []
            excluded_count = 0

            for dr in dose_responses:
                if dr.exclude:
                    excluded_count += 1
                    continue

                concs.append(dr.concentration)
                responses.append(dr.response)

            logger.info(f"Result {result.id}: {excluded_count} excluded, {len(concs)} remaining")

            total_excluded += excluded_count
            total_results_processed += 1

            # Recalculate km, vmax, r_squared
            if len(concs) > 1:
                try:
                    concs = np.array(concs)
                    responses = np.array(responses)
                    vmax, km = utils.mm.calculate_km(responses, concs)
                    r_squared = utils.mm.r_squared(responses, utils.mm.curve(concs, vmax, km))
                    result.km = km
                    result.vmax = vmax
                    result.r_squared = r_squared
                    session.add(result)
                    logger.info(f"Recalculated result {result.id}: km={km:.2f}, vmax={vmax:.2f}, r2={r_squared:.2f}")
                except Exception as e:
                    logger.warning(f"Failed to recalculate for result {result.id}: {e}")
                    result.km = None
                    result.vmax = None
                    result.r_squared = None
                    session.add(result)
            else:
                logger.warning(f"Not enough data to recalculate result {result.id}")
                result.km = None
                result.vmax = None
                result.r_squared = None
                session.add(result)

            session.commit()

    logger.info(f"Total results processed: {total_results_processed}")
    logger.info(f"Total exclusions made: {total_excluded}")
    logger.info("Processing complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply anomaly detection to database results")
    parser.add_argument('--model_path', type=str, required=True, help='Path to trained model')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout rate used in model')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for anomaly detection (lower = less conservative)')
    args = parser.parse_args()
    main(args)