# Slurm planning specification

## Purpose
Render validated `sbatch` scripts from structured job specifications while enforcing cluster policy.

## Responsibilities
- Map job spec fields (partition, nodes, ntasks, gpus, etc.) to Slurm `#SBATCH` directives.
- Apply defaults from policy snapshots when fields are omitted.
- Verify generated scripts against required checklists before returning.
- Produce directive-level rationales for auditing.

## Interface
```python
class SlurmPlanner:
    def __init__(self, policy: dict, logger: AuditLogger | None = None): ...
    def make_sbatch(self, spec: dict, kind: str = "cpu") -> Path: ...
    def validate_sbatch(self, script: Path) -> list[ValidationIssue]: ...
```

### `make_sbatch`
- Consumes job specs following `tests/11_job_plan_slurm/data/job_inputs_cpu.json` or `job_inputs_gpu.json`.
- Uses policy data shaped like `tests/11_job_plan_slurm/data/policy_snapshot.json`.
- Writes scripts under `runs/<timestamp>/slurm/` with filenames `job_cpu.sbatch` or `job_gpu.sbatch`.
- Captures directive rationales referencing `tests/11_job_plan_slurm/data/directive_rationale.md`.

### `validate_sbatch`
- Runs structural checks aligned with `tests/11_job_plan_slurm/expected/basic_sbatch_checklist.md` and `gpu_sbatch_checklist.md`.
- Returns a list of issues; empty list indicates success.
- Emits validation reports similar to `tests/11_job_plan_slurm/expected/validation_report_template.json`.

## Logging
- Store generated scripts and SHA256 hashes in `events.jsonl`.
- Record validation results (issues, notes) referencing the template JSON files.
- Include directive rationales in the audit log with `source` and `reason` fields.
