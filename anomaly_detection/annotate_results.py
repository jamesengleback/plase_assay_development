import os
import sqlite3
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Spectral Classifier for 350-450 nm region
class SpectralClassifier(nn.Module):
    def __init__(self, input_length=101, dropout=0.5):
        super(SpectralClassifier, self).__init__()
        self.conv1 = nn.Conv1d(1, 16, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(16)
        self.conv2 = nn.Conv1d(16, 32, kernel_size=5, stride=1, padding=2)
        self.bn2 = nn.BatchNorm1d(32)
        self.pool = nn.AdaptiveAvgPool1d(1)  # Global avg pooling
        self.fc = nn.Linear(32, 1)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        x = x.unsqueeze(1)  # Add channel dim: [batch, 1, 101]
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool(x).squeeze(-1)  # [batch, 32]
        x = self.dropout(x)
        x = self.fc(x)
        return x

def load_data(data_path):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    return df

def prepare_result_features(df):
    result_features = []
    for result_id, group in df.groupby('result_id'):
        accepted = group['accepted'].iloc[0]
        locked = group['locked'].iloc[0]
        label = 1 if not accepted else 0  # Anomaly if not accepted
        
        # Compute difference spectra per concentration in 350-450 nm
        spectra_diffs = []
        for conc, conc_group in group.groupby('compound_concentration'):
            # Wavelengths start from 220 at column 13, so 350 is at 13 + (350-220) = 143
            wl_start = 13 + (350 - 220)  # 143
            wl_end = 13 + (450 - 220) + 1  # 244
            test_data = conc_group[conc_group['well_type'] == 'test'].iloc[:, wl_start:wl_end].mean()
            control_data = conc_group[conc_group['well_type'] == 'control'].iloc[:, wl_start:wl_end].mean()
            if not test_data.empty and not control_data.empty:
                diff = test_data - control_data
                # Baseline correction at 800 nm if available, else skip
                baseline_idx = 13 + (800 - 220)  # 593
                if baseline_idx < len(diff):
                    diff_corrected = diff - diff.iloc[baseline_idx]
                else:
                    diff_corrected = diff
                spectra_diffs.append(diff_corrected.values)
        
        # Aggregate: Mean spectrum across concentrations
        if spectra_diffs:
            mean_spectrum = np.mean(spectra_diffs, axis=0)
        else:
            mean_spectrum = np.zeros(101)  # 350-450 nm
        
        # Normalize by protein concentration (optional)
        prot_conc = group['protein_concentration'].mean()
        if prot_conc > 0:
            mean_spectrum /= prot_conc
        
        result_features.append({
            'result_id': result_id,
            'features': mean_spectrum,  # Shape: [101]
            'accepted': accepted,
            'locked': locked
        })
    
    return result_features

class ResultDataset(torch.utils.data.Dataset):
    def __init__(self, result_features):
        self.data = result_features
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        features = torch.tensor(self.data[idx]['features'], dtype=torch.float32)
        return features

def parse_args():
    parser = argparse.ArgumentParser(description="Annotate database with anomaly predictions")
    parser.add_argument('--data_path', type=str, default='data.csv', help='Path to data file (CSV)')
    parser.add_argument('--model_path', type=str, default='runs_spectral/20251213_232136/model.pth', help='Path to the trained model')
    parser.add_argument('--db_path', type=str, default='../api/database.db', help='Path to database')
    parser.add_argument('--certainty_threshold', type=float, default=0.6, help='Certainty threshold for locking')
    parser.add_argument('--dropout', type=float, default=0.3, help='Dropout rate (must match trained model)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting annotation with args: {args}")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load data
    df = load_data(args.data_path)
    logger.info(f"Loaded data from {args.data_path}")
    
    # Prepare features for all results
    result_features = prepare_result_features(df)
    logger.info(f"Prepared {len(result_features)} result features")
    
    # Load model
    input_length = len(result_features[0]['features'])
    model = SpectralClassifier(input_length=input_length, dropout=args.dropout)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model = model.to(device)
    model.eval()
    logger.info(f"Loaded model from {args.model_path}")
    
    # Predict
    dataset = ResultDataset(result_features)
    loader = torch.utils.data.DataLoader(dataset, batch_size=16, shuffle=False)
    
    all_probs = []
    with torch.no_grad():
        for features in loader:
            features = features.to(device)
            outputs = model(features)
            probs = torch.sigmoid(outputs).squeeze()
            all_probs.extend(probs.cpu().numpy())
    
    certainties = 2 * np.abs(np.array(all_probs) - 0.5)
    
    # Update database
    with sqlite3.connect(args.db_path) as conn:
        cursor = conn.cursor()
        for i, item in enumerate(result_features):
            result_id = item['result_id']
            prob = all_probs[i]
            certainty = certainties[i]
            prediction = prob > 0.5  # True if anomaly
            
            # Lock and set accepted based on prediction
            accepted = not prediction  # accepted=True if not anomaly
            locked = True
            cursor.execute("UPDATE result SET accepted = ?, locked = ? WHERE id = ?", (accepted, locked, result_id))
            logger.info(f"Updated result {result_id}: accepted={accepted}, locked={locked}, certainty={certainty:.3f}")
        
        conn.commit()
    
    logger.info("Annotation completed")