#!/bin/bash
#SBATCH --job-name=sample
#SBATCH --time=00:10:00
#SBATCH --partition=boost_usr_dbg

srun ./build/sample
