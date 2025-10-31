# Tinygrad Setup Notes

1. Clone the repository:
   ```
   git clone https://github.com/geohot/tinygrad.git
   ```
2. Enter the repository and install dependencies in editable mode:
   ```
   pip install -e .
   ```
3. Run the smoke tests to verify the install:
   ```
   python3 test/test_ops.py --quick
   ```
4. For GPU runs on Leonardo, load `nvhpc/23.3` and request the `booster` partition.
5. Submit jobs with `sbatch --test-only scripts/run_tinygrad.sbatch` when validating on the login node.
