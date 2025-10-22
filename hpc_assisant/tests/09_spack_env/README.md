# Suite 09 – Spack environment

This suite verifies the agent can detect and operate within Spack environments, from planning concretization to validating activation effects.

## Suite contents
- **T-0901-detect-spack-yaml** – Identify `spack.yaml` in a project and draft a concretize/activate plan capturing compilers and variants.
- **T-0902-spack-activate** – Activate the environment and confirm binaries are exposed to subprocesses with recorded environment deltas.

## Shared prerequisites
- Sample `spack.yaml` under `data/`.
- Access to `spack` command (or mocked output) within the allow list.
- Run directories ready to store plans under `runs/<timestamp>/spack/`.

## High-level manual procedure
1. Place the sample project in the workspace as described in `plan.md`.
2. Run the detection and planning steps to produce `spack_plan.json`.
3. Simulate or perform activation, capturing environment changes into `env_delta.json`.
4. Compare results with expectations in `expected/`.

## Supporting documentation
- `plan.md` outlines detection/activation steps and promotion criteria for `utils/spack`.
- `data/` includes representative manifests and command templates.
- `expected/` provides reference JSON outputs and environment deltas.
- `risks.md` documents common pitfalls such as concretization failures or conflicting module loads.
