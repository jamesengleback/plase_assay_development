import os
import subprocess
import time

# Small hyperparameter sweep for spectral anomaly detector
lrs = [0.001, 0.0005]
dropouts = [0.3, 0.5]
gammas = [2.0, 3.0]
batch_sizes = [16, 32]

total_runs = len(lrs) * len(dropouts) * len(gammas) * len(batch_sizes)
run_count = 0

for lr in lrs:
    for dropout in dropouts:
        for gamma in gammas:
            for batch_size in batch_sizes:
                run_count += 1
                print(f"Run {run_count}/{total_runs}: lr={lr}, dropout={dropout}, gamma={gamma}, batch_size={batch_size}")
                
                cmd = [
                    'python', 'spectral_anomaly_detector.py',
                    '--lr', str(lr),
                    '--dropout', str(dropout),
                    '--gamma', str(gamma),
                    '--batch_size', str(batch_size),
                    '--epochs', '10'  # More epochs for sweep
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd='/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development/anomaly_detection')
                    print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                    if result.stderr:
                        print("STDERR:", result.stderr[-500:])
                    print(f"Return code: {result.returncode}")
                except Exception as e:
                    print(f"Error: {e}")
                
                time.sleep(1)  # Brief pause

print("Sweep completed.")