# GPU utilities specification

## Purpose
Detect available GPU resources and translate findings into Slurm request flags.

## Responsibilities
- Run detection commands (`nvidia-smi`, `rocm-smi`) and parse results.
- Compare detected hardware with requested resources.
- Generate Slurm flag recommendations (`--gpus`, `--gres`, `--constraint`).

## Interface
```python
class GPUHelper:
    def detect_gpu(self) -> dict: ...
    def slurm_gpu_flags(self, count: int, constraints: dict | None = None) -> dict: ...
```

### `detect_gpu`
- Produces structure described by `tests/20_gpu_job/expected/detect_template.json`.
- Logs detection timestamp and source command outputs.

### `slurm_gpu_flags`
- Uses policy data to format flags (e.g., `--gres=gpu:a100:2`).
- Returns dictionary with `flags` and `rationale`.

## Logging
- Log detection output and chosen flags for audit and troubleshooting.
