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
    parser = argparse.ArgumentParser(description="Variance-based Anomaly Detection for P450 Results")
    parser.add_argument('--data_path', type=str, default='data.csv', help='Path to data file (CSV)')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--output_path', type=str, default='results_variance.txt', help='Path to save results')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout rate')
    parser.add_argument('--gamma', type=float, default=2.0, help='Gamma for FocalLoss')
    return parser.parse_args()

# Load and process data
def load_data(data_path):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    return df

# Prepare features per result
def prepare_result_features(df):
    result_features = []
    for result_id, group in df.groupby('result_id'):
        accepted = group['accepted'].iloc[0]
        label = 1 if not accepted else 0  # Anomaly if not accepted
        
        # Dose response features
        dr_group = group.drop_duplicates(subset=['compound_concentration'])
        concs = dr_group['compound_concentration'].values
        responses = dr_group['response'].values
        dr_excludes = dr_group['exclude'].values
        
        num_dr = len(concs)
        mean_resp = np.mean(responses) if len(responses) > 0 else 0
        std_resp = np.std(responses) if len(responses) > 1 else 0
        num_excl_dr = np.sum(dr_excludes)
        
        # Collect all absorbance data
        test_410 = []
        control_410 = []
        test_abs_350_450 = []
        control_abs_350_450 = []
        protein_concs = []
        
        for _, row in group.iterrows():
            protein_conc = row['protein_concentration']
            protein_concs.append(protein_conc)
            well_type = row['well_type']
            
            if 410 in row.index and not pd.isna(row[410]):
                if well_type == 'test':
                    test_410.append(row[410])
                elif well_type == 'control':
                    control_410.append(row[410])
            
            # For 350-450
            for wl in range(350, 451):
                if wl in row.index and not pd.isna(row[wl]):
                    if well_type == 'test':
                        test_abs_350_450.append(row[wl])
                    elif well_type == 'control':
                        control_abs_350_450.append(row[wl])
        
        # Variance at 410 nm between test and control, normalized by protein concentration
        if len(test_410) == len(control_410) and len(test_410) > 0:
            diffs = np.array(test_410) - np.array(control_410)
            var_410 = np.var(diffs)
            mean_prot = np.mean(protein_concs) if protein_concs else 1
            norm_var_410 = var_410 / mean_prot if mean_prot > 0 else var_410
        else:
            norm_var_410 = 0.0
        
        # Additional trace features: mean absorbance in 350-450 for test and control
        mean_test_abs = np.mean(test_abs_350_450) if test_abs_350_450 else 0
        mean_control_abs = np.mean(control_abs_350_450) if control_abs_350_450 else 0
        
        features = [
            num_dr,
            mean_resp,
            std_resp,
            num_excl_dr,
            norm_var_410,
            mean_test_abs,
            mean_control_abs
        ]
        
        result_features.append({
            'result_id': result_id,
            'features': features,
            'label': label
        })
    
    return result_features

# Dataset
class ResultDataset(Dataset):
    def __init__(self, result_features):
        self.data = result_features
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        features = torch.tensor(self.data[idx]['features'], dtype=torch.float32)
        label = torch.tensor(self.data[idx]['label'], dtype=torch.float32)
        return features, label

# Simple MLP Classifier
class SimpleClassifier(nn.Module):
    def __init__(self, input_dim, dropout=0.5):
        super(SimpleClassifier, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.bn1 = nn.BatchNorm1d(64)
        self.fc2 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.fc3 = nn.Linear(32, 1)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        x = torch.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = torch.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = self.fc3(x)
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

# Training
def train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, num_epochs, writer, run_dir, device):
    model.train()
    best_val_loss = float('inf')
    try:
        for epoch in range(num_epochs):
            epoch_loss = 0
            for features, labels in train_loader:
                features, labels = features.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(features)
                loss = criterion(outputs.squeeze(), labels)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg_train_loss = epoch_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {avg_train_loss:.4f}")
            writer.add_scalar('Loss/train', avg_train_loss, epoch)
            writer.add_scalar('LR', optimizer.param_groups[0]['lr'], epoch)
            
            # Validation
            model.eval()
            val_loss = 0
            all_preds = []
            all_labels = []
            all_probs = []
            with torch.no_grad():
                for features, labels in val_loader:
                    features, labels = features.to(device), labels.to(device)
                    outputs = model(features)
                    loss = criterion(outputs.squeeze(), labels)
                    val_loss += loss.item()
                    probs = torch.sigmoid(outputs).squeeze()
                    preds = probs > 0.5
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(labels.cpu().numpy())
                    all_probs.extend(probs.cpu().numpy())
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
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
            
            scheduler.step(avg_val_loss)
            
            model.train()
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        torch.save(model.state_dict(), os.path.join(run_dir, 'interrupted_model.pth'))
        logger.info(f"Model saved at interruption: {os.path.join(run_dir, 'interrupted_model.pth')}")
        sys.exit(0)
    
    torch.save(model.state_dict(), os.path.join(run_dir, 'final_model.pth'))
    logger.info("Final model saved")
    return model, best_val_loss

# Evaluation
def evaluate_model(model, test_loader, test_features, writer, epoch, device):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    with torch.no_grad():
        for features, labels in test_loader:
            features, labels = features.to(device), labels.to(device)
            outputs = model(features)
            probs = torch.sigmoid(outputs).squeeze()
            preds = probs > 0.5
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    acc = accuracy_score(all_labels, all_preds)
    prec = precision_score(all_labels, all_preds, zero_division=0)
    rec = recall_score(all_labels, all_preds, zero_division=0)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    
    best_prec = 0
    best_thresh = 0.5
    for thresh in np.arange(0.1, 0.9, 0.1):
        preds_tuned = np.array(all_probs) > thresh
        prec_tuned = precision_score(all_labels, preds_tuned, zero_division=0)
        if prec_tuned > best_prec:
            best_prec = prec_tuned
            best_thresh = thresh
    
    logger.info(f"Best threshold: {best_thresh}, Precision: {best_prec:.2f}")
    
    # Compute certainties
    certainties = 2 * np.abs(np.array(all_probs) - 0.5)
    
    # Save predictions with certainties
    result_ids = [item['result_id'] for item in test_features]
    df_preds = pd.DataFrame({
        'result_id': result_ids,
        'probability': all_probs,
        'certainty': certainties,
        'prediction': all_preds,
        'label': all_labels
    })
    df_preds.to_csv('prediction_certainties.csv', index=False)
    logger.info("Saved prediction certainties to prediction_certainties.csv")
    
    try:
        auc_score = roc_auc_score(all_labels, all_probs)
        writer.add_pr_curve('PR Curve', np.array(all_labels), np.array(all_probs), epoch)
        return acc, prec, rec, f1, auc_score, best_thresh
    except:
        return acc, prec, rec, f1, None, best_thresh

# Main
if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting variance-based anomaly detection with args: {args}")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = f"runs_variance/{run_id}"
    os.makedirs(run_dir, exist_ok=True)
    logger.info(f"Run directory created: {run_dir}")
    
    writer = SummaryWriter(log_dir=os.path.join(run_dir, 'tensorboard'))
    
    writer.add_text('Hyperparameters', str(vars(args)), 0)
    hyperparams = vars(args).copy()
    hyperparams['run_id'] = run_id
    hyperparams['run_dir'] = run_dir
    with open(os.path.join(run_dir, 'hyperparameters.txt'), 'w') as f:
        for key, value in hyperparams.items():
            f.write(f"{key}: {value}\n")
    
    try:
        df = load_data(args.data_path)
        logger.info(f"Loaded data from {args.data_path}")
        
        features_path = 'result_features.csv'
        if os.path.exists(features_path):
            logger.info(f"Loading features from {features_path}")
            df_features = pd.read_csv(features_path)
            result_features = []
            for _, row in df_features.iterrows():
                features = [row[f'f{i}'] for i in range(7)]
                result_features.append({'result_id': row['result_id'], 'features': features, 'label': row['label']})
        else:
            logger.info("Preparing result features...")
            result_features = prepare_result_features(df)
            logger.info(f"Saving features to {features_path}")
            df_features = pd.DataFrame({
                'result_id': [item['result_id'] for item in result_features],
                'label': [item['label'] for item in result_features],
                'f0': [item['features'][0] for item in result_features],
                'f1': [item['features'][1] for item in result_features],
                'f2': [item['features'][2] for item in result_features],
                'f3': [item['features'][3] for item in result_features],
                'f4': [item['features'][4] for item in result_features],
                'f5': [item['features'][5] for item in result_features],
                'f6': [item['features'][6] for item in result_features]
            })
            df_features.to_csv(features_path, index=False)
        
        logger.info(f"Prepared {len(result_features)} result features")
        
        # Split
        train_features, test_features = train_test_split(result_features, test_size=0.2, random_state=42)
        train_features, val_features = train_test_split(train_features, test_size=0.25, random_state=42)  # 60% train, 20% val, 20% test
        
        train_dataset = ResultDataset(train_features)
        val_dataset = ResultDataset(val_features)
        test_dataset = ResultDataset(test_features)
        
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
        
        input_dim = len(result_features[0]['features'])
        model = SimpleClassifier(input_dim, dropout=args.dropout)
        model = model.to(device)
        writer.add_text('Model Architecture', str(model), 0)
        
        all_labels = [item['label'] for item in train_features]
        num_anomalies = sum(all_labels)
        if num_anomalies == 0:
            logger.error("No anomalies in training data")
            raise ValueError("No anomalies in training set")
        pos_weight = (len(all_labels) - num_anomalies) / num_anomalies
        pos_weight = torch.tensor(pos_weight, dtype=torch.float32)
        criterion = FocalLoss(alpha=pos_weight.item(), gamma=args.gamma)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
        
        model, best_val_loss = train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, args.epochs, writer, run_dir, device)
        
        # Save the trained model
        model_path = os.path.join(run_dir, 'model.pth')
        torch.save(model.state_dict(), model_path)
        logger.info(f"Model saved to {model_path}")
        
        hyperparams['best_val_loss'] = best_val_loss
        with open(os.path.join(run_dir, 'hyperparameters.txt'), 'w') as f:
            for key, value in hyperparams.items():
                f.write(f"{key}: {value}\n")
        
        summary_file = 'runs_variance/runs_summary.txt'
        os.makedirs('runs_variance', exist_ok=True)
        with open(summary_file, 'a') as f:
            f.write(f"{run_id}: {run_dir}, best_val_loss: {best_val_loss:.4f}\n")
        
        acc, prec, rec, f1, auc, best_thresh = evaluate_model(model, test_loader, test_features, writer, args.epochs, device)
        
        writer.add_scalar('Accuracy/test', acc, args.epochs)
        writer.add_scalar('Precision/test', prec, args.epochs)
        writer.add_scalar('Recall/test', rec, args.epochs)
        writer.add_scalar('F1/test', f1, args.epochs)
        if auc is not None:
            writer.add_scalar('AUC/test', auc, args.epochs)
        
        results = f"Variance-based Detection - Acc: {acc:.2f}, Prec: {prec:.2f}, Rec: {rec:.2f}, F1: {f1:.2f}"
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