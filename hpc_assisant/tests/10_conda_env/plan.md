# Execution plan – Suite 10_conda_env

## Goal
Verify Conda environments are detected, provisioned if necessary, and used for isolated command execution.

## Tests included
1. **T-1001-detect-conda**
   - **Input**: manifest `data/environment.yml`.
   - **Steps**:
     1. Check for `environment.yml` at project root.
     2. Parse name, channels, and dependencies into metadata.
     3. Store metadata in `runs/<timestamp>/conda/env_detect.json`.
   - **Done when**:
     - Metadata matches `expected/env_detect.json` structure.
     - Audit log records manifest checksum.

2. **T-1002-conda-run-noninteractive**
   - **Input**: command template in `data/conda_commands.md`.
   - **Steps**:
     1. Create or cache the environment using `conda env create` or `conda env update`.
     2. Execute target command via `conda run` (non-interactive) without altering parent shell.
     3. Capture command output and environment diff to `runs/<timestamp>/conda/run_output.txt` and `env_delta.json`.
   - **Done when**:
     - Command succeeds and finds required interpreter/libraries.
     - Diff shows expected path updates consistent with `expected/env_delta.json`.
     - Audit log confirms no persistent shell modifications.

## Promotion to utils/
- **utils/conda**
  - `has_env(path: Path) -> bool`
  - `create_or_cache(env_file: Path) -> dict`
  - `run_in_env(env_name: str, command: list[str]) -> dict`

Promote once tests pass and documentation covers:
- Handling of environment reuse vs. recreation (timestamped caches).
- Non-interactive execution strategy (`conda run`, `micromamba run`).
- Cleanup policy for temporary prefixes.
