# Suite 04 – CMake build

This suite exercises configuration and compilation workflows for CMake-based HPC projects, ensuring the agent can generate reproducible build artifacts and logs.

## Suite contents
- **T-0401-configure** – Run `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` on the toy repository and capture configuration outputs.
- **T-0402-build** – Execute `cmake --build build --parallel` and record build artifacts, timing, and success status.

## Shared prerequisites
- Access to a CMake-enabled environment (module load instructions provided in suite 03).
- Sample repository prepared according to `data/project_source.md`.
- Writable workspace under the run directory to store `build/` and logs.

## High-level manual procedure
1. Prepare the project workspace following `plan.md`.
2. Run the configuration step, ensuring logs and cache files are stored under `runs/<timestamp>/cmake_config/`.
3. Trigger the build step, archiving build output in `runs/<timestamp>/cmake_build/`.
4. Compare artifacts and logs against the expectations in `expected/`.

## Supporting documentation
- `plan.md` outlines step-by-step actions and promotion criteria for `utils/build_cmake`.
- `data/` holds source preparation notes and command templates.
- `expected/` contains log templates and the required artifact checklist.
- `risks.md` highlights typical CMake pitfalls and recovery guidance.
