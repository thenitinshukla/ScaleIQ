# Suite 08 – GPU error triage

This suite captures GPU-specific compiler failures (CUDA and ROCm) and ensures the agent recommends safe fixes.

## Suite contents
- **T-0801-nvcc-arch-mismatch** – Detect `nvcc fatal : Unsupported gpu architecture` and suggest compatible `-gencode` flags or CUDA module updates.
- **T-0802-rocm-offload-arch** – Detect missing `--offload-arch` flags in clang/hipcc output and recommend appropriate options.

## Shared prerequisites
- Sample GPU build logs placed under `data/`.
- Triage rule set in `utils/triage` extended for GPU categories.
- Audit workspace ready to persist outputs in `runs/<timestamp>/triage/`.

## High-level manual procedure
1. Feed the failing log from `data/` into the triage workflow described in `plan.md`.
2. Capture the structured diagnosis as JSON under the run directory.
3. Compare the output with the reference JSON files in `expected/` to confirm category, rule ID, and advice.

## Supporting documentation
- `plan.md` defines the execution order and promotion criteria for GPU triage rules.
- `data/` provides CUDA and ROCm failure examples.
- `expected/` contains canonical triage outputs per case.
- `risks.md` notes pitfalls such as architecture naming differences or mixed log formats.
