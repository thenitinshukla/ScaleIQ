# Tinygrad Setup Notes

1. Clone the repository:
   ```
   git clone https://github.com/geohot/tinygrad.git
   ```
2. Enter the repository and install dependencies in editable mode:
   ```
   pip install -e .
   ```
   If `pip` is unavailable on the login node, use `python3 -m pip install -e .` or activate an existing environment before installing.
3. Run the smoke tests to verify the install:
   ```
   python3 test/test_ops.py --quick
   ```
4. On Leonardo, first check availability with `module avail nvhpc` and load the current version (e.g., `module load nvhpc/22.11`) before running GPU workflows.
5. Submit jobs with `sbatch --test-only scripts/run_tinygrad.sbatch` when validating on the login node; the script can live under `scripts/run_tinygrad.sbatch`.
6. Inspect the repository with `ls`, `cat README.md`, and similar commands before applying changes.
