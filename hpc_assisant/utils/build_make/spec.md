# Make build utilities specification

## Purpose
Provide a stable interface around GNU Make builds with controlled parallelism and artifact capture.

## Responsibilities
- Execute `make` targets with configurable `-j` values and working directories.
- Capture stdout/stderr, exit codes, and timings for audit logging.
- Collect resulting artifacts and compute checksums.

## Interface
```python
class MakeBuilder:
    def __init__(self, logger: AuditLogger): ...
    def run(self, path: Path, target: str | None = None, jobs: int | None = None, extra_args: list[str] | None = None) -> dict: ...
    def collect_artifacts(self, path: Path, patterns: list[str]) -> list[dict]: ...
```

### `run`
- Builds command `make [-jN] [target] [extra_args...]`.
- Returns dict with command, exit code, duration, stdout/stderr paths.
- Applies dry-run logic when in safety mode.

### `collect_artifacts`
- Matches files relative to project root using glob patterns (defaults: `solver`, `*.a`, `*.so`).
- Copies/symlinks to run artifact directory and records checksums (`sha256`).

## Logging
- Emit events to `runs/<timestamp>/events.jsonl` for each make invocation.
- Metrics stored in `runs/<timestamp>/make_build/metrics.json` (duration, jobs, targets).
- Preserve build log under `make_build/build.log` with redacted environment variables.
