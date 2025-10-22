# Audit logging specification

## Purpose
Provide structured logging utilities that capture every agent action with proper redaction and hashing.

## Responsibilities
- Emit JSON Lines events conforming to `tests/16_audit_logging/data/event_schema.json`.
- Redact sensitive information according to `data/redaction_rules.md`.
- Compute and include hashes for outputs and artifacts.
- Manage log rotation and summary reports.

## Interface
```python
class AuditLogger:
    def __init__(self, run_id: str, events_path: Path): ...
    def log_event(self, event: dict) -> None: ...
    def redact(self, payload: Any) -> Any: ...
    def rotate(self) -> Path: ...
```

### `log_event`
- Validates input against schema.
- Appends to `events.jsonl` and flushes to disk.

### `redact`
- Applies masking rules and returns sanitized payloads similar to `expected/redaction_output.json`.

### `rotate`
- Optionally rotate logs, updating metadata and returning new path.

## Integration
- Other utils call `log_event` for start/success/failure statuses.
- Redaction used before logging raw command outputs or environment data.
