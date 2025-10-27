#!/bin/bash
# Placeholder launch script used for dry-run validation on Leonardo.
set -euo pipefail

module purge
module load nvhpc/23.3

echo "Would launch the hybrid simulation with nvprof disabled for dry run."
