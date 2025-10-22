# Conda command sequence

1. Create or update environment
   ```bash
   conda env update -f environment.yml --prune
   ```
2. Run command non-interactively
   ```bash
   conda run --name hpc-agent python -c "import mpi4py, numpy; print('ok')"
   ```
3. Verify parent shell unaffected
   ```bash
   echo $PATH  # should remain unchanged
   ```
