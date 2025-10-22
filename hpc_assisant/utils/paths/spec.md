# RunPaths specification

## Purpose
Standardize directory and file naming for per-run artifacts.

## Responsibilities
- Generate timestamped run directories under `runs/`.
- Provide helper methods to reference common files: `env.json`, `events.jsonl`, `report.md`, `artifacts/`.
- Ensure directories are created with private permissions (mode 700).

## Interface
```python
class RunPaths:
    def __init__(self, root: Path): ...
    @classmethod
    def create(cls, root: Path | None = None) -> "RunPaths": ...
    @property
    def env_file(self) -> Path: ...
    @property
    def events_log(self) -> Path: ...
    @property
    def report(self) -> Path: ...
    def ensure_artifacts_dir(self) -> Path: ...
```

## Naming convention
- `runs/YYYYMMDD-HHMMSS/` as default folder.
- Support optional suffixes (e.g., `-retry01`).

## Logging
- Emit creation events with directory path and timestamp.
