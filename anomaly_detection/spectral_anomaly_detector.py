import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score
import argparse
import logging
from torch.utils.tensorboard import SummaryWriter
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Focal Loss for imbalanced data
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
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

# Spectral Classifier for 350-450 nm region
class SpectralClassifier(nn.Module):
    def __init__(self, input_length=101, dropout=0.3):
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
            wl_end = 13 + (450 - 220) + 1  # 244 (inclusive)
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
            'label': label,
            'accepted': accepted,
            'locked': locked
        })
    
    return result_features

class ResultDataset(Dataset):
    def __init__(self, result_features):
        self.data = result_features
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        features = torch.tensor(self.data[idx]['features'], dtype=torch.float32)
        label = torch.tensor(self.data[idx]['label'], dtype=torch.float32)
        return features, label

def train_model(model, train_loader, val_loader, device, epochs=10, lr=0.001, weight_decay=1e-4, gamma=2.0, patience=5):
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    
    # Calculate pos_weight for Focal Loss
    labels = []
    for _, label in train_loader:
        labels.extend(label.numpy())
    pos_weight = len([l for l in labels if l == 0]) / len([l for l in labels if l == 1]) if sum(labels) > 0 else 1
    criterion = FocalLoss(alpha=pos_weight, gamma=gamma)
    
    writer = SummaryWriter()
    best_auc = 0
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for features, labels in train_loader:
            features, labels = features.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs.squeeze(), labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_preds = []
        val_labels = []
        with torch.no_grad():
            for features, labels in val_loader:
                features, labels = features.to(device), labels.to(device)
                outputs = model(features)
                probs = torch.sigmoid(outputs.squeeze())
                val_preds.extend(probs.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())
        
        val_auc = roc_auc_score(val_labels, val_preds) if len(set(val_labels)) > 1 else 0
        val_f1 = f1_score(val_labels, np.round(val_preds))
        val_precision = precision_score(val_labels, np.round(val_preds), zero_division=0)
        val_recall = recall_score(val_labels, np.round(val_preds), zero_division=0)
        
        writer.add_scalar('Loss/train', train_loss / len(train_loader), epoch)
        writer.add_scalar('AUC/val', val_auc, epoch)
        writer.add_scalar('F1/val', val_f1, epoch)
        
        logger.info(f"Epoch {epoch+1}/{epochs}: Train Loss={train_loss/len(train_loader):.4f}, Val AUC={val_auc:.4f}, F1={val_f1:.4f}, Prec={val_precision:.4f}, Rec={val_recall:.4f}")
        
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            torch.save(model.state_dict(), 'best_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping")
                break
    
    writer.close()
    return best_auc

def evaluate_model(model, test_loader, device):
    model.eval()
    preds = []
    labels = []
    certainties = []
    with torch.no_grad():
        for features, label in test_loader:
            features, label = features.to(device), label.to(device)
            outputs = model(features)
            probs = torch.sigmoid(outputs.squeeze())
            preds.extend(probs.cpu().numpy())
            labels.extend(label.cpu().numpy())
            certainties.extend(2 * np.abs(probs.cpu().numpy() - 0.5))
    
    auc = roc_auc_score(labels, preds) if len(set(labels)) > 1 else 0
    f1 = f1_score(labels, np.round(preds))
    precision = precision_score(labels, np.round(preds), zero_division=0)
    recall = recall_score(labels, np.round(preds), zero_division=0)
    
    logger.info(f"Test AUC={auc:.4f}, F1={f1:.4f}, Prec={precision:.4f}, Rec={recall:.4f}")
    
    # Save predictions
    results_df = pd.DataFrame({
        'prediction': preds,
        'certainty': certainties,
        'label': labels
    })
    results_df.to_csv('prediction_certainties.csv', index=False)
    
    return auc, f1

def parse_args():
    parser = argparse.ArgumentParser(description="Train spectral anomaly detector")
    parser.add_argument('--data_path', type=str, default='data.csv', help='Path to data file (CSV)')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--dropout', type=float, default=0.3, help='Dropout rate')
    parser.add_argument('--gamma', type=float, default=2.0, help='Focal Loss gamma')
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='L2 regularization')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting training with args: {args}")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load data
    df = load_data(args.data_path)
    logger.info(f"Loaded data from {args.data_path}")
    
    # Prepare features
    result_features = prepare_result_features(df)
    logger.info(f"Prepared {len(result_features)} result features")
    
    # Split data
    train_features, test_features = train_test_split(result_features, test_size=0.2, random_state=42, stratify=[f['label'] for f in result_features])
    train_features, val_features = train_test_split(train_features, test_size=0.25, random_state=42, stratify=[f['label'] for f in train_features])
    
    train_dataset = ResultDataset(train_features)
    val_dataset = ResultDataset(val_features)
    test_dataset = ResultDataset(test_features)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Model
    input_length = len(result_features[0]['features'])
    model = SpectralClassifier(input_length=input_length, dropout=args.dropout)
    
    # Train
    start_time = time.time()
    best_auc = train_model(model, train_loader, val_loader, device, epochs=args.epochs, lr=args.lr, weight_decay=args.weight_decay, gamma=args.gamma)
    train_time = time.time() - start_time
    logger.info(f"Training completed in {train_time:.2f}s, Best Val AUC: {best_auc:.4f}")
    
    # Load best model and evaluate
    model.load_state_dict(torch.load('best_model.pth'))
    evaluate_model(model, test_loader, device)
    
    # Save final model
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs('runs_spectral', exist_ok=True)
    final_path = f'runs_spectral/{timestamp}/model.pth'
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    torch.save(model.state_dict(), final_path)
    logger.info(f"Saved model to {final_path}")