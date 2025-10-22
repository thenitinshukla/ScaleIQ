# Execution plan – Suite 09_spack_env

## Goal
Ensure the agent can recognize Spack environments, plan concretization, and activate them while tracking environment changes.

## Tests included
1. **T-0901-detect-spack-yaml**
   - **Input**: manifest in `data/spack.yaml`.
   - **Steps**:
     1. Inspect project root for `spack.yaml`.
     2. Parse packages, compilers, and variants into a plan object.
     3. Save the plan to `runs/<timestamp>/spack/spack_plan.json`.
   - **Done when**:
     - Plan matches `expected/spack_plan.json` structure.
     - Compilers and variants are enumerated.
     - Audit log records manifest hash and detection outcome.

2. **T-0902-spack-activate**
   - **Input**: activation instructions in `data/spack_commands.md`.
   - **Steps**:
     1. Run `spack env activate --sh` (or mocked equivalent) to capture environment mutations.
     2. Snapshot environment before/after activation.
     3. Compute diff and store in `runs/<timestamp>/spack/env_delta.json`.
   - **Done when**:
     - Diff matches `expected/env_delta.json` format.
     - Key binaries (e.g., `mpicc`) become visible to child processes.
     - Audit log includes command outputs and masking of any tokens.

## Promotion to utils/
- **utils/spack**
  - `has_env(path: Path) -> bool`
  - `concretize(path: Path) -> dict`
  - `activate(path: Path) -> dict`

Promote once tests pass and documentation covers:
- Handling remote binaries vs. dry-run mode when `spack` unavailable.
- Storage of concretization logs (`spack install --only dependencies` is not run yet but planned).
- Reversion strategy for environment changes (e.g., `spack env deactivate`).
