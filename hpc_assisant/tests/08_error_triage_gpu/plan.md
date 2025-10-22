# Execution plan – Suite 08_error_triage_gpu

## Goal
Extend error triage to cover GPU compiler failures and provide actionable adjustments.

## Tests included
1. **T-0801-nvcc-arch-mismatch**
   - **Input**: CUDA build log in `data/nvcc_arch_mismatch.log`.
   - **Steps**:
     1. Run the triage routine on the log.
     2. Save the result to `runs/<timestamp>/triage/T-0801-nvcc-arch-mismatch.json`.
     3. Confirm the advice suggests compatible `-gencode` flags or updated CUDA module.
   - **Done when**:
     - Output matches `expected/nvcc_arch_mismatch.json`.
     - Advice references supported architectures and module version.
     - Confidence meets or exceeds the threshold defined in suite 06.

2. **T-0802-rocm-offload-arch**
   - **Input**: HIP/ROCm build log in `data/rocm_offload_missing.log`.
   - **Steps**:
     1. Execute triage on the log.
     2. Store results under `runs/<timestamp>/triage/T-0802-rocm-offload-arch.json`.
     3. Ensure advice proposes the correct `--offload-arch` flag.
   - **Done when**:
     - Output matches `expected/rocm_offload_arch.json`.
     - Advice includes at least one architecture hint (e.g., `gfx90a`).
     - Audit entry records captured architecture keywords.

## Promotion to utils/
- **utils/triage** – add GPU rules:
  - `gpu.unsupported_architecture`
  - `gpu.missing_offload_arch`
- Document architecture mapping logic and confidence scoring in the spec.

Promote once both tests pass and documentation covers:
- Canonical architecture names for CUDA (`sm_80`, `sm_90`) and ROCm (`gfx90a`, `gfx1100`).
- Fallback behaviour when device detection is unavailable.
- Logging schema additions for GPU triage (e.g., `detected_target`, `suggested_flags`).
