#!/bin/bash

# Hyperparameter sweep script for anomaly detection
# Runs 8 configurations with 10 epochs each

cd /home/james/thesis-stuff/old/201906_P450_PlateAssay_Development/anomaly_detection

PYTHON_CMD="/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development/venv/bin/python"

# Configuration 1
echo "Running config 1: lr=1e-4, gamma=1, pair_penalty_weight=0.5, dropout=0.3"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-4 --gamma 1 --pair_penalty_weight 0.5 --dropout 0.3

# Configuration 2
echo "Running config 2: lr=1e-3, gamma=2, pair_penalty_weight=1.0, dropout=0.5"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-3 --gamma 2 --pair_penalty_weight 1.0 --dropout 0.5

# Configuration 3
echo "Running config 3: lr=1e-2, gamma=3, pair_penalty_weight=2.0, dropout=0.5"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-2 --gamma 3 --pair_penalty_weight 2.0 --dropout 0.5

# Configuration 4
echo "Running config 4: lr=1e-4, gamma=2, pair_penalty_weight=1.0, dropout=0.3"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-4 --gamma 2 --pair_penalty_weight 1.0 --dropout 0.3

# Configuration 5
echo "Running config 5: lr=1e-3, gamma=1, pair_penalty_weight=2.0, dropout=0.5"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-3 --gamma 1 --pair_penalty_weight 2.0 --dropout 0.5

# Configuration 6
echo "Running config 6: lr=1e-2, gamma=1, pair_penalty_weight=0.5, dropout=0.3"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-2 --gamma 1 --pair_penalty_weight 0.5 --dropout 0.3

# Configuration 7
echo "Running config 7: lr=1e-4, gamma=3, pair_penalty_weight=2.0, dropout=0.5"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-4 --gamma 3 --pair_penalty_weight 2.0 --dropout 0.5

# Configuration 8
echo "Running config 8: lr=1e-3, gamma=3, pair_penalty_weight=0.5, dropout=0.3"
$PYTHON_CMD anomaly_detection_script.py --epochs 10 --lr 1e-3 --gamma 3 --pair_penalty_weight 0.5 --dropout 0.3

echo "Hyperparameter sweep completed. Check runs/runs_summary.txt for results."