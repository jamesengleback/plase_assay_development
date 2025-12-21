import argparse
import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, f1_score
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import ReduceLROnPlateau
import logging
from datetime import datetime
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Argument parser
def parse_args():
    parser = argparse.ArgumentParser(description="Anomaly Detection for P450 Plate Assay Traces using CNN")
    parser.add_argument('--data_path', type=str, default='data.csv', help='Path to data file (CSV or SQLite database)')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--batch_size', type=int, default=1, help='Batch size (keep 1 for variable groups)')
    parser.add_argument('--output_path', type=str, default='results.txt', help='Path to save results')
    parser.add_argument('--gamma', type=float, default=2.0, help='Gamma for FocalLoss')
    parser.add_argument('--pair_penalty_weight', type=float, default=1.0, help='Pair penalty weight')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout rate')
    return parser.parse_args()

# Load and process data
def load_data(data_path):
    if data_path.endswith('.csv'):
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")
        df = pd.read_csv(data_path)
    else:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Database file not found: {data_path}")
        sql = """
        select 
        experiment_id,
        dr.result_id,
        w.id as well_id,
        w.address,
        r.accepted,
        r.locked,
        w.compound_concentration,
        dr.exclude,
        dr.response,
        w.protein_concentration,
        w.volume,
        wr.well_type,
        group_concat(distinct ra.comment) as comments,
        group_concat(a.wavelength) as wavelength,
        group_concat(a.absorbance) as absorbance
        from well w
        join wellresultlink wr
        on wr.well_id = w.id
        join result r
        on r.id = wr.result_id
        join doseresponse dr
        on dr.result_id = wr.result_id and dr.concentration = w.compound_concentration
        left join resultannotation ra
        on ra.result_id = r.id
        join absorbance a
        on a.well_id = w.id
        group by w.id
        """
        with sqlite3.connect(data_path) as con:
            df = pd.read_sql(sql, con)
        
        # Process absorbance
        o = []
        for _, row in df.iterrows():
            o.append(dict(zip(
                    list(map(lambda i: int(float(i)), row['wavelength'].split(','))),
                    row['absorbance'].split(','))
                         ))
        o = pd.DataFrame(o).astype(float)
        df = pd.concat([df, o], axis=1)
        df = df.drop(['wavelength', 'absorbance'], axis=1)
    return df

# Group data and prepare pairs
def prepare_trace_data(df):
    trace_data = []
    for result_id, group in df.groupby('result_id'):
        # Group by concentration
        conc_groups = group.groupby('compound_concentration')
        for conc, conc_group in conc_groups:
            well_types = conc_group['well_type'].unique()
            if len(well_types) == 2:  # Assume test and control
                test_group = conc_group[conc_group['well_type'] == 'test']
                control_group = conc_group[conc_group['well_type'] == 'control']
                if not test_group.empty and not control_group.empty:
                    # For each test-control pair
                    for _, test_row in test_group.iterrows():
                        test_spec = test_row.loc[300:800].values.astype(float)
                        test_label = test_row['exclude']
                        control_row = control_group.iloc[0]  # Assume one control per conc
                        control_spec = control_row.loc[300:800].values.astype(float)
                        diff_spec = test_spec - control_spec
                        combined_spec = np.stack([test_spec, diff_spec])  # Shape: (2, 501)
                        pair_excluded = test_row['exclude'] or control_row['exclude']  # If either is excluded
                        trace_data.append({
                            'spectra': combined_spec,
                            'label': test_label,
                            'pair_id': f"{result_id}_{conc}",
                            'pair_excluded': pair_excluded
                        })
                    # Similarly for control
                    for _, control_row in control_group.iterrows():
                        control_spec = control_row.loc[300:800].values.astype(float)
                        test_row = test_group.iloc[0]
                        test_spec = test_row.loc[300:800].values.astype(float)
                        diff_spec = control_spec - test_spec
                        combined_spec = np.stack([control_spec, diff_spec])
                        pair_excluded = control_row['exclude'] or test_row['exclude']
                        trace_data.append({
                            'spectra': combined_spec,
                            'label': control_row['exclude'],
                            'pair_id': f"{result_id}_{conc}",
                            'pair_excluded': pair_excluded
                        })
    return trace_data

# Dataset and DataLoader
class TraceDataset(Dataset):
    def __init__(self, trace_data, oversample_anomalies=True, augment=True):
        self.data = []
        for item in trace_data:
            spectra = torch.tensor(item['spectra'], dtype=torch.float32).unsqueeze(0)  # (1, 2, 501)
            label = torch.tensor(item['label'], dtype=torch.float32)
            pair_id = item['pair_id']
            pair_excluded = item['pair_excluded']
            self.data.append((spectra, label, pair_id, pair_excluded))
            # Oversample anomalies
            if oversample_anomalies and label == 1:
                for _ in range(2):
                    augmented_spectra = spectra + torch.randn_like(spectra) * 0.01 if augment else spectra
                    self.data.append((augmented_spectra, label, pair_id, pair_excluded))
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]

def collate_fn(batch):
    spectra = [item[0] for item in batch]
    labels = torch.stack([item[1] for item in batch])
    pair_ids = [item[2] for item in batch]
    pair_excludeds = torch.tensor([item[3] for item in batch], dtype=torch.float32)
    return spectra, labels, pair_ids, pair_excludeds

def collate_fn(batch):
    spectra = [item[0] for item in batch]
    labels = torch.stack([item[1] for item in batch])
    pair_ids = [item[2] for item in batch]
    pair_excludeds = torch.tensor([item[3] for item in batch], dtype=torch.float32)
    return spectra, labels, pair_ids, pair_excludeds

# CNN Model
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
        x = self.pool(x)  # (batch, 32, 1)
        x = torch.relu(self.conv2(x))  # conv2 takes (batch, 32, 1)
        x = self.pool(x)  # (batch, 64, 1)
        x = torch.relu(self.conv3(x))  # conv3 takes (batch, 64, 1)
        x = self.pool(x)  # (batch, 128, 1)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.fc(x)
        return x

# Focal Loss
class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        bce_loss = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-bce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        return focal_loss

# Pair-Aware Loss
class PairAwareLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2.0, pair_penalty_weight=1.0):
        super(PairAwareLoss, self).__init__()
        self.focal_loss = FocalLoss(alpha=alpha, gamma=gamma)
        self.pair_penalty_weight = pair_penalty_weight
    
    def forward(self, outputs, labels, pair_ids, pair_excludeds):
        # Focal loss for individual predictions
        focal = self.focal_loss(outputs, labels)
        
        # Pair penalty: For excluded pairs, penalize if no anomaly is predicted
        pair_penalty = 0.0
        unique_pairs = set(pair_ids)
        for pid in unique_pairs:
            indices = [i for i, p in enumerate(pair_ids) if p == pid]
            if len(indices) > len(outputs):
                continue  # Skip if mismatch
            pair_outputs = outputs[indices]
            pair_preds = torch.sigmoid(pair_outputs) > 0.5
            pair_excluded = pair_excludeds[indices[0]]  # Assume same for pair
            if pair_excluded == 1 and not any(pair_preds):
                pair_penalty += self.pair_penalty_weight  # Penalty for missing anomaly in excluded pair
        
        return focal + pair_penalty

# Training
def train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, num_epochs, writer, run_dir):
    model.train()
    best_val_loss = float('inf')
    accumulation_steps = 1  # Simulate batch_size=4
    try:
        for epoch in range(num_epochs):
            epoch_loss = 0
            for i, (spectra_batch, labels_batch, pair_ids_batch, pair_excludeds_batch) in enumerate(train_loader):
                for spectra, labels, pair_ids, pair_excludeds in zip(spectra_batch, labels_batch, pair_ids_batch, pair_excludeds_batch):
                    optimizer.zero_grad()
                    outputs = model(spectra)
                    loss = criterion(outputs.squeeze(0), labels.unsqueeze(0), [pair_ids], pair_excludeds.unsqueeze(0)) / accumulation_steps
                    loss.backward()
                    if (i+1) % accumulation_steps == 0:
                        optimizer.step()
                        optimizer.zero_grad()
                        epoch_loss += loss.item()
            avg_train_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {avg_train_loss:.4f}")
            writer.add_scalar('Loss/train', avg_train_loss, epoch)
            writer.add_scalar('LR', optimizer.param_groups[0]['lr'], epoch)
            # Log histograms of model weights
            for name, param in model.named_parameters():
                writer.add_histogram(f'Weights/{name}', param, epoch)
            
            # Validation
            model.eval()
            val_loss = 0
            all_preds = []
            all_labels = []
            all_probs = []
            with torch.no_grad():
                for spectra_batch, labels_batch, pair_ids_batch, pair_excludeds_batch in val_loader:
                    for spectra, labels, pair_ids, pair_excludeds in zip(spectra_batch, labels_batch, pair_ids_batch, pair_excludeds_batch):
                        outputs = model(spectra)
                        loss = criterion(outputs.squeeze(0), labels.unsqueeze(0), [pair_ids], pair_excludeds.unsqueeze(0))
                        val_loss += loss.item()
                        probs = torch.sigmoid(outputs).squeeze()
                        preds = probs > 0.5
                        all_preds.append(preds.item())
                        all_labels.append(labels.item())
                        all_probs.append(probs.item())
            avg_val_loss = val_loss / len(val_loader)
            acc = accuracy_score(all_labels, all_preds)
            prec = precision_score(all_labels, all_preds, zero_division=0)
            rec = recall_score(all_labels, all_preds, zero_division=0)
            f1 = f1_score(all_labels, all_preds, zero_division=0)
            try:
                auc_score = roc_auc_score(all_labels, all_probs)
            except:
                auc_score = None
            logger.info(f"Epoch {epoch+1:2d}/{num_epochs:2d} | Val Loss: {avg_val_loss:6.4f} | Acc: {acc:5.2f} | Prec: {prec:5.2f} | Rec: {rec:5.2f} | F1: {f1:5.2f}" + (f" | AUC: {auc_score:5.2f}" if auc_score is not None else ""))
            writer.add_scalar('Loss/val', avg_val_loss, epoch)
            writer.add_scalar('Accuracy/val', acc, epoch)
            writer.add_scalar('Precision/val', prec, epoch)
            writer.add_scalar('Recall/val', rec, epoch)
            writer.add_scalar('F1/val', f1, epoch)
            if auc_score is not None:
                writer.add_scalar('AUC/val', auc_score, epoch)
            
            # Track best val loss
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
            
            scheduler.step(avg_val_loss)
            
            model.train()
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        # Save current model
        torch.save(model.state_dict(), os.path.join(run_dir, 'interrupted_model.pth'))
        logger.info(f"Model saved at interruption: {os.path.join(run_dir, 'interrupted_model.pth')}")
        logger.info(f"Most recent best validation loss: {best_val_loss:.4f}")
        sys.exit(0)
    
    # Save final model
    torch.save(model.state_dict(), os.path.join(run_dir, 'final_model.pth'))
    logger.info("Final model saved")
    return model, best_val_loss

# Evaluation
def evaluate_model(model, test_loader, writer, epoch):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    with torch.no_grad():
        for spectra_batch, labels_batch, _, _ in test_loader:
            for spectra, labels in zip(spectra_batch, labels_batch):
                outputs = model(spectra)
                probs = torch.sigmoid(outputs).squeeze()
                preds = probs > 0.5  # Default threshold
                all_preds.append(preds.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
                all_probs.append(probs.cpu().numpy())
    
    num_positives = sum(all_labels)
    if num_positives == 0:
        logger.warning("No positive labels in test set, AUC cannot be computed")
    
    # Compute metrics at default threshold
    acc = accuracy_score(all_labels, all_preds)
    prec = precision_score(all_labels, all_preds, zero_division=0)
    rec = recall_score(all_labels, all_preds, zero_division=0)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    
    # Threshold tuning for better precision
    best_prec = 0
    best_thresh = 0.5
    for thresh in np.arange(0.1, 0.9, 0.1):
        preds_tuned = np.array(all_probs) > thresh
        prec_tuned = precision_score(all_labels, preds_tuned, zero_division=0)
        if prec_tuned > best_prec:
            best_prec = prec_tuned
            best_thresh = thresh
    
    logger.info(f"Best threshold: {best_thresh}, Precision: {best_prec:.2f}")
    
    try:
        auc_score = roc_auc_score(all_labels, all_probs)
        writer.add_pr_curve('PR Curve', np.array(all_labels), np.array(all_probs), epoch)
        return acc, prec, rec, f1, auc_score, best_thresh
    except:
        return acc, prec, rec, f1, None, best_thresh

# Main
if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting anomaly detection with args: {args}")
    
    # Create unique run directory
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = f"runs/{run_id}"
    os.makedirs(run_dir, exist_ok=True)
    logger.info(f"Run directory created: {run_dir}")
    
    writer = SummaryWriter(log_dir=os.path.join(run_dir, 'tensorboard'))
    
    # Log hyperparameters
    writer.add_text('Hyperparameters', str(vars(args)), 0)
    hyperparams = vars(args).copy()
    hyperparams['run_id'] = run_id
    hyperparams['run_dir'] = run_dir
    with open(os.path.join(run_dir, 'hyperparameters.txt'), 'w') as f:
        for key, value in hyperparams.items():
            f.write(f"{key}: {value}\n")
    
    try:
        # Load data
        df = load_data(args.data_path)
        logger.info(f"Loaded {len(df)} traces from {args.data_path}")
        
        trace_data = prepare_trace_data(df)
        logger.info(f"Prepared {len(trace_data)} individual traces with pair context")
        
        # Split into train/val/test based on result_id
        result_ids = list(set([item['pair_id'].split('_')[0] for item in trace_data]))
        train_result_ids, val_test_result_ids = train_test_split(result_ids, test_size=0.4, random_state=42)
        val_result_ids, test_result_ids = train_test_split(val_test_result_ids, test_size=0.5, random_state=42)
        train_data = [item for item in trace_data if item['pair_id'].split('_')[0] in train_result_ids]
        val_data = [item for item in trace_data if item['pair_id'].split('_')[0] in val_result_ids]
        test_data = [item for item in trace_data if item['pair_id'].split('_')[0] in test_result_ids]
        logger.info(f"Split into {len(train_data)} train traces, {len(val_data)} val traces, and {len(test_data)} test traces")
        
        # Datasets and loaders
        train_dataset = TraceDataset(train_data)
        val_dataset = TraceDataset(val_data, oversample_anomalies=False, augment=False)  # No oversample/augment for val
        test_dataset = TraceDataset(test_data, oversample_anomalies=False, augment=False)  # No oversample/augment for test
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)
        test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)
        logger.info("Data loaders created")
        
        # Model, loss, optimizer
        model = CNNAnomalyDetector(dropout=args.dropout)
        writer.add_text('Model Architecture', str(model), 0)
        all_labels = [item['label'] for item in train_data]
        num_anomalies = sum(all_labels)
        if num_anomalies == 0:
            logger.error("No anomalies in training data, cannot compute pos_weight")
            raise ValueError("No anomalies in training set")
        pos_weight = (len(all_labels) - num_anomalies) / num_anomalies
        pos_weight = torch.tensor(pos_weight, dtype=torch.float32)
        criterion = PairAwareLoss(alpha=pos_weight.item(), gamma=args.gamma, pair_penalty_weight=args.pair_penalty_weight)
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
        logger.info(f"Model created with pos_weight {pos_weight:.2f}")
        
        # Train
        logger.info("Starting training")
        model, best_val_loss = train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, args.epochs, writer, run_dir)
        logger.info("Training completed")
        
        # Update hyperparameters file with best val loss
        hyperparams['best_val_loss'] = best_val_loss
        with open(os.path.join(run_dir, 'hyperparameters.txt'), 'w') as f:
            for key, value in hyperparams.items():
                f.write(f"{key}: {value}\n")
        
        # Update global runs summary
        summary_file = 'runs/runs_summary.txt'
        os.makedirs('runs', exist_ok=True)
        with open(summary_file, 'a') as f:
            f.write(f"{run_id}: {run_dir}, best_val_loss: {best_val_loss:.4f}\n")
        logger.info(f"Run summary updated in {summary_file}")
        
        # Evaluate
        logger.info("Starting evaluation")
        acc, prec, rec, f1, auc, best_thresh = evaluate_model(model, test_loader, writer, args.epochs)
        logger.info("Evaluation completed")
        
        writer.add_scalar('Accuracy/test', acc, args.epochs)
        writer.add_scalar('Precision/test', prec, args.epochs)
        writer.add_scalar('Recall/test', rec, args.epochs)
        writer.add_scalar('F1/test', f1, args.epochs)
        if auc is not None:
            writer.add_scalar('AUC/test', auc, args.epochs)
        
        results = f"CNN Detection - Acc: {acc:.2f}, Prec: {prec:.2f}, Rec: {rec:.2f}, F1: {f1:.2f}"
        if auc is not None:
            results += f", AUC: {auc:.2f}"
        results += f", Best Threshold: {best_thresh}"
        
        print(results)
        with open(args.output_path, 'w') as f:
            f.write(results)
        logger.info(f"Results saved to {args.output_path}")
    
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
    finally:
        writer.close()