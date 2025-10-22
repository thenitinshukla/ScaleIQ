# CMake build utilities specification

## Purpose
Automate configuration and compilation steps for CMake projects while capturing reproducible metadata.

## Responsibilities
- Configure projects with specified flags and environment metadata.
- Execute builds with controllable parallelism.
- Collect resulting artifacts and metrics (timings, cache summaries, checksums).

## Interface
```python
class CMakeBuilder:
    def __init__(self, logger: AuditLogger, env: EnvManager): ...
    def configure(self, source: Path, build: Path, flags: list[str]) -> dict: ...
    def build(self, build: Path, target: str | None = None, parallel: int | None = None) -> dict: ...
    def collect_artifacts(self, build: Path, destination: Path, patterns: list[str] | None = None) -> list[dict]: ...
```

### `configure`
- Runs `cmake -S <source> -B <build>` plus provided flags.
- Returns dict with cache path, generator, compiler info, duration, exit code.
- Captures stdout/stderr paths in result.

### `build`
- Runs `cmake --build <build> [--target <target>] [--parallel N]`.
- Returns dict with exit code, duration, log paths.

### `collect_artifacts`
- Identifies binaries/libraries in the build directory (respecting patterns or defaults like `*.exe`, `*.so`, `*.a`).
- Copies or symlinks to destination and records checksums.

## Logging
- Every command logs to `events.jsonl` with command, flags, duration, exit code, stdout/stderr hashes.
- Metrics persisted to `runs/<timestamp>/cmake_build/metrics.json`.
