# Slurm runtime utilities specification

## Purpose
Submit Slurm jobs, monitor their lifecycle, and collect generated artifacts while emitting auditable logs.

## Responsibilities
- Wrap `sbatch` submission and return structured metadata (JobID, script path, stdout/stderr locations).
- Poll `squeue`/`sacct` according to configurable intervals to build a state timeline.
- Gather job output files, compute hashes, and store manifests under run directories.
- Handle timeouts, retries, and optional cancellation of stuck jobs.

## Interface
```python
class SlurmRunner:
    def __init__(self, policy: dict, logger: AuditLogger | None = None): ...
    def submit(self, script: Path, extra_env: Mapping[str, str] | None = None) -> dict: ...
    def wait(self, job_id: str, config: dict) -> list[dict]: ...
    def collect(self, job_id: str, submission: dict, dest: Path) -> dict: ...
```

### `submit`
- Expects scripts validated by `slurm_plan`.
- Executes commands described in `tests/12_job_submit_monitor/data/submit_sequence.md`.
- Returns metadata shaped like `tests/12_job_submit_monitor/expected/submission_template.json`.
- Logs JobID, submission host, and raw command output.

### `wait`
- Uses polling configuration compatible with `tests/12_job_submit_monitor/data/monitor_config.json`.
- Records each observation as an event dictionary appended to a timeline (see `job_timeline_sample.jsonl`).
- Detects timeouts and performs `scancel` if `timeout_action` is set.

### `collect`
- Reads log paths from submission metadata and follows the steps in `data/artifact_collection.md`.
- Copies artifacts into `dest` (usually `runs/<ts>/slurm_run/artifacts/`).
- Returns manifest shaped like `tests/12_job_submit_monitor/expected/artifact_manifest.json`.

## Logging
- Write submission metadata to `submission.json` and timeline events to `job.jsonl`.
- Emit artifact manifest and hash records in audit log entries.
- Redact sensitive environment variables before logging command invocations.
