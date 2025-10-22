# Cluster policy specification

## Purpose
Load and validate cluster policy data (partitions, QoS, accounts) to ensure job plans comply with Leonardo rules.

## Responsibilities
- Load policy snapshot JSON and provide accessors.
- Validate job specifications against partition limits and account requirements.
- Surface diagnostics for missing or invalid fields.

## Interface
```python
class PolicyManager:
    def __init__(self, policy_path: Path): ...
    def load_policy(self) -> dict: ...
    def validate_request(self, spec: dict) -> list[dict]: ...
```

### `load_policy`
- Reads snapshots shaped like `tests/18_policy_leonardo/expected/policy_snapshot_example.json`.
- Tracks provenance metadata.

### `validate_request`
- Checks job specs (e.g., from `job_inputs_cpu.json`) against policy limits and accounts.
- Returns issues similar to `tests/18_policy_leonardo/expected/account_diagnostics.json`.

## Logging
- Log policy load timestamp and source.
- Record validation diagnostics in audit log for each job plan.
