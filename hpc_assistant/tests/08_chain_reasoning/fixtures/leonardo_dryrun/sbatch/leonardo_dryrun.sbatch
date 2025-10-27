#!/bin/bash
#SBATCH --job-name=leonardo-dryrun
#SBATCH --partition=booster
#SBATCH --nodes=1
#SBATCH --time=00:10:00
#SBATCH --gpus-per-node=1

echo "Dry-run submission: No commands executed on compute nodes."
