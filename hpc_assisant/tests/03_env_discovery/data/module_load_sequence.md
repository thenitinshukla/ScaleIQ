# Module load sequence

1. Ensure the module system is initialized (`source /etc/profile.d/modules.sh` if required).
2. Load modules in the following order:
   ```bash
   module load gcc/12.1.0
   module load openmpi/4.1.5
   module load cmake/3.26.4
   ```
3. Record the command sequence and any warnings in the audit log.
4. After loading, run child checks:
   ```bash
   which gcc
   which mpicc
   ```
5. If modules are unavailable, document the fallback or alternative versions used.
