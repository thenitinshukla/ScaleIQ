# Repository utilities specification

## Purpose
Manage cloning and build-system detection in a repeatable manner.

## Responsibilities
- Clone repositories into sanitized scratch directories.
- Capture metadata (URL, ref, commit SHA, workspace path).
- Detect build-system indicators and language hints.

## Interface
```python
class RepoManager:
    def __init__(self, scratch_root: Path): ...
    def clone(self, url: str, ref: str | None = None) -> dict: ...
    def detect_buildsystem(self, path: Path) -> dict: ...
```

### `clone`
- Creates a workspace under the scratch root with timestamp suffix.
- Supports local mirrors when URLs are not reachable.
- Returns `{ "path": str, "sha": str, "ref": str }`.

### `detect_buildsystem`
- Scans for known indicators listed in `tests/02_repo_detect/data/build_indicators.md`.
- Reports `{ "type": "cmake|make|unknown", "languages": [ {"name": str, "percentage": int } ], "evidence": [str], "notes": str }`.

## Logging
- Write clone metadata to `runs/<timestamp>/repo.json`.
- Record detection output in `runs/<timestamp>/detection.json`.
