# Suite 10 – Conda environment

This suite confirms the agent can detect Conda environment manifests and execute commands within the environment without polluting the parent session.

## Suite contents
- **T-1001-detect-conda** – Identify `environment.yml` and record essential metadata.
- **T-1002-conda-run-noninteractive** – Run a command within the environment in a non-interactive subshell, confirming interpreter/package availability and isolation.

## Shared prerequisites
- Sample `environment.yml` stored in `data/`.
- Access to `conda` or `mamba` commands within the allow list (mockable if unavailable).
- Run workspace ready to capture detection metadata and command output under `runs/<timestamp>/conda/`.

## High-level manual procedure
1. Detect the environment file and produce metadata as described in `plan.md`.
2. Create or reuse the environment per instructions, recording actions.
3. Execute the non-interactive command, capturing stdout/stderr and environment diffs.
4. Validate results against `expected/` artifacts.

## Supporting documentation
- `plan.md` details the detection/run steps and promotion criteria for `utils/conda`.
- `data/` houses the manifest and command templates.
- `expected/` includes metadata templates, run logs, environment diffs, and logging requirements.
- `risks.md` highlights common issues such as env name collisions or shell contamination.
