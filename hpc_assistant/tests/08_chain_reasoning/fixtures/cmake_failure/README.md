# Failing Build Example

This project requires `module load nvhpc/23.3` before configuration.

## Build
1. `cmake -S . -B build`
2. `cmake --build build`

If CMake fails due to missing CUDA toolkit, load the module and rerun.
