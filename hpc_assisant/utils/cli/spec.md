# CLI utilities specification

## Purpose
Provide parsing and command dispatch helpers for the `hpc-agent` CLI.

## Responsibilities
- Define CLI commands, global options, and help text.
- Support dry-run mode and configuration overrides.
- Translate CLI invocations into internal actions or API calls.

## Interface
```python
class CLI:
    def parse_args(self, argv: list[str]) -> argparse.Namespace: ...
    def dispatch(self, args: argparse.Namespace) -> int: ...
```

### `parse_args`
- Implements spec in `tests/23_cli_api_surface/data/cli_spec.md`.
- Ensures commands `plan`, `run`, `resume` share global options.

### `dispatch`
- Routes commands to appropriate services (planner, runner, resume).
- Supports dry-run semantics by toggling execution mode.

## Logging
- Log command entry/exit in audit log, including dry-run flag status.
