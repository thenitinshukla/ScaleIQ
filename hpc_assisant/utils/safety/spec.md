# Safety utilities specification

## Purpose
Restrict command execution to an allowlist and provide dry-run simulations for destructive actions.

## Responsibilities
- Load allowlist definitions and rationales.
- Evaluate commands before execution, returning allow/deny decisions with explanations.
- Provide dry-run wrappers that detail simulated actions without modifying the filesystem.
- Expose sandbox paths for validation.

## Interface
```python
class SafetyGuard:
    def __init__(self, allowlist: dict, sandbox: list[Path]): ...
    def is_allowed(self, command: list[str]) -> tuple[bool, str]: ...
    def as_dry_run(self, command: list[str]) -> dict: ...
    def sandbox_paths(self) -> list[Path]: ...
```

### `is_allowed`
- Validates command against data in `tests/15_security_allowlist/data/allowlist.yaml`.
- Returns `(allowed, message)` aligning with `expected/allowlist_responses.json`.

### `as_dry_run`
- Simulates actions per `data/dry_run_scenarios.json`.
- Outputs report similar to `expected/dry_run_report_template.json`.

## Logging
- Record decisions in audit log, including command, status, and rationale.
- Flag any attempts to execute denied commands.
