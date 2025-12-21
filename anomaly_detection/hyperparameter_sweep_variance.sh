#!/bin/bash

# Hyperparameter sweep for variance-based anomaly detector

# Parameters to sweep (reduced set based on prior results)
lrs=(0.001 0.0005)
dropouts=(0.3 0.5)
batch_sizes=(16 32)
gammas=(2.0 3.0)

# Fixed
epochs=20
data_path="data.csv"

for lr in "${lrs[@]}"; do
    for dropout in "${dropouts[@]}"; do
        for batch_size in "${batch_sizes[@]}"; do
            for gamma in "${gammas[@]}"; do
                echo "Running with lr=$lr, dropout=$dropout, batch_size=$batch_size, gamma=$gamma"
                python variance_anomaly_detector.py \
                    --data_path $data_path \
                    --epochs $epochs \
                    --lr $lr \
                    --batch_size $batch_size \
                    --dropout $dropout \
                    --gamma $gamma
            done
        done
    done
done

echo "Sweep complete"