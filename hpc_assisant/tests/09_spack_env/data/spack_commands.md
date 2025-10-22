# Spack command sequence

1. Detect environment
   ```bash
   spack env status
   ```
2. Concretize
   ```bash
   spack -e . concretize --fresh
   ```
3. Activate (shell)
   ```bash
   eval "$(spack env activate --sh .)"
   ```
4. Verify binaries
   ```bash
   which mpicc
   mpicc --version
   ```
