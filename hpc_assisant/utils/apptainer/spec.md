# Apptainer utilities specification

## Purpose
Build and execute containerized workflows using Apptainer for reproducible HPC environments.

## Responsibilities
- Build `.sif` images from definition files.
- Manage build logs, checksums, and artifact storage.
- Execute commands within containers with required bind mounts.
- Capture runtime outputs and return status/metrics.

## Interface
```python
class ApptainerRunner:
    def build(self, def_file: Path, output: Path, options: dict | None = None) -> dict: ...
    def exec(self, image: Path, command: list[str], binds: list[str], env: dict | None = None) -> dict: ...
```

### `build`
- Implements instructions in `tests/17_apptainer/data/build_instructions.md`.
- Returns metadata matching `tests/17_apptainer/expected/image_manifest.json`.

### `exec`
- Executes runtime commands per `data/runtime_commands.md`.
- Captures stdout/stderr and verifies bind mounts.

## Logging
- Log build/exec steps through `AuditLogger`, including checksums and exit codes.
- Store logs under `runs/<timestamp>/apptainer/`.
