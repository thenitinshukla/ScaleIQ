# Conda utilities specification

## Purpose
Handle detection, creation/caching, and isolated command execution for Conda environments.

## Responsibilities
- Detect `environment.yml` manifests and extract metadata (name, channels, dependencies).
- Create or reuse environments while recording actions and hashes.
- Run commands via `conda run` (or equivalent) without mutating the parent shell.

## Interface
```python
class CondaEnv:
    def __init__(self, logger: AuditLogger): ...
    def has_env(self, path: Path) -> bool: ...
    def create_or_cache(self, env_file: Path, force: bool = False) -> dict: ...
    def run_in_env(self, env_name: str, command: list[str], workdir: Path | None = None) -> dict: ...
```

### `create_or_cache`
- Executes `conda env update -f` (or `micromamba create`) and stores solver duration.
- Returns metadata with environment prefix, solver stats, and actions taken (`created`, `updated`, `skipped`).

### `run_in_env`
- Uses `conda run --name <env>` to execute commands.
- Captures stdout/stderr, exit code, and environment diff relative to the parent shell.

## Logging
- Follow the structure documented in `tests/10_conda_env/expected/logging_requirements.md`.
- Detection metadata written to `runs/<timestamp>/conda/env_detect.json`.
- Command outputs stored under `runs/<timestamp>/conda/run_output.txt` with corresponding `env_delta.json`.
- All operations logged in `events.jsonl` including hashes of manifests and command transcripts.
