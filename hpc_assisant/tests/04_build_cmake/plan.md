# Execution plan – Suite 04_build_cmake

## Goal
Validate that the agent can configure and build a CMake project in a controlled workspace, collecting reproducible artifacts and logs.

## Tests included
1. **T-0401-configure**
   - **Input**: prepared source tree documented in `data/project_source.md`; configuration flags from `data/cmake_flags.md`.
   - **Steps**:
     1. Ensure required modules are loaded (see `data/prereq_modules.txt`).
     2. Create a clean build directory (`build/`) within the run workspace.
     3. Run `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` plus additional flags from the data file.
     4. Store `CMakeCache.txt`, stdout, stderr, and timing in `runs/<timestamp>/cmake_config/`.
   - **Done when**:
     - `CMakeCache.txt` and `build/` exist with expected entries.
     - Configuration log matches the format in `expected/config_log_template.txt`.
     - Audit log records command, duration, and exit code 0.

2. **T-0402-build**
   - **Input**: configured build directory from T-0401.
   - **Steps**:
     1. Run `cmake --build build --parallel` (parallelism per `data/build_parallelism.md`).
     2. Capture stdout/stderr to `runs/<timestamp>/cmake_build/build.log`.
     3. Collect resulting binaries or libraries into `runs/<timestamp>/cmake_build/artifacts/` (symlink or copy).
     4. Compute checksums for produced artifacts.
   - **Done when**:
     - Build completes with exit code 0.
     - Artifact list matches `expected/artifact_manifest.json`.
     - Timing and checksum data recorded in `runs/<timestamp>/cmake_build/metrics.json`.

## Promotion to utils/
- **utils/build_cmake**
  - `configure(source: Path, build: Path, flags: list[str]) -> dict`
  - `build(build: Path, target: str | None = None, parallel: int | None = None) -> dict`
  - `collect_artifacts(build: Path, destination: Path) -> list`

Promote once tests pass and documentation includes:
- Handling of generator selection (default Ninja/Unix Makefiles).
- Environment requirements (compilers, modules) and how to report missing tools.
- Logging expectations: stdout/stderr capture, timings, cache snapshots.
