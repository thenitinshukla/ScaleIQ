# Environment utilities specification

## Purpose
Interact with the module system and compute environment diffs for reproducibility.

## Responsibilities
- Query module availability and versions.
- Load modules using `modulecmd` while updating the current process environment.
- Compare environment snapshots and produce structured diffs.

## Interface
```python
class EnvManager:
    def module_query(self, names: list[str]) -> dict: ...
    def module_load(self, modules: list[str]) -> dict: ...
    def env_diff(self, before: Mapping[str, str], after: Mapping[str, str]) -> dict: ...
```

### `module_query`
- Runs `module spider` (or equivalent) and returns data shaped like `tests/03_env_discovery/expected/modules_sample.json`.

### `module_load`
- Invokes `modulecmd python load ...`.
- Returns the updated environment mapping.
- Emits warnings if requested modules are missing.
- Logs the sequence described in `tests/03_env_discovery/data/module_load_sequence.md`.

### `env_diff`
- Accepts two environment mappings and returns a diff matching `tests/03_env_discovery/expected/env_delta_template.json`.
- Focuses on `PATH`, `LD_LIBRARY_PATH`, `MODULEPATH`, `CPATH`, `PKG_CONFIG_PATH`.

## Logging
- Persist module query results as `modules.json`.
- Persist environment diffs as `env_delta.json` with `_metadata` references to snapshots.
