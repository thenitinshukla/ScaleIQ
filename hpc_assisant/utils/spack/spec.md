# Spack utilities specification

## Purpose
Detect and manage project-specific Spack environments, including concretization planning and activation.

## Responsibilities
- Locate `spack.yaml` manifests and parse key metadata (specs, compilers, variants).
- Plan concretization commands and store reproducible plans with manifest hashes.
- Activate environments and surface environment deltas for audit logs.

## Interface
```python
class SpackEnv:
    def __init__(self, logger: AuditLogger): ...
    def has_env(self, path: Path) -> bool: ...
    def concretize(self, path: Path, flags: list[str] | None = None) -> dict: ...
    def activate(self, path: Path) -> dict: ...
```

### `concretize`
- Runs `spack -e <path> concretize` with optional flags.
- Returns dict containing manifest hash, specs, compilers, variants, and command logs.

### `activate`
- Evaluates `spack env activate --sh <path>` and captures environment before/after snapshots.
- Returns diff structure suitable for `expected/env_delta.json`.

## Logging
- Plans stored under `runs/<timestamp>/spack/spack_plan.json`.
- Activation deltas stored under `runs/<timestamp>/spack/env_delta.json` with references to snapshots.
- Record executed commands, exit codes, and stdout/stderr hashes in `events.jsonl`.
