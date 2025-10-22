# Report generation specification

## Purpose
Produce end-of-run summaries consolidating build, job, and diagnostic data.

## Responsibilities
- Aggregate information from manifests, logs, metrics, and policy checks.
- Populate report template sections with consistent formatting.
- Highlight next actions or unresolved issues.

## Interface
```python
class ReportGenerator:
    def __init__(self, template: Path): ...
    def make_report(self, run_dir: Path, context: dict) -> Path: ...
```

### `make_report`
- Uses template similar to `tests/24_e2e_pipeline_smallrepo/expected/report_template.md`.
- Injects context values (toolchain, job id, metrics).
- Writes `report.md` into run directory and returns path.

## Logging
- Record report generation event with summary metrics and hash of report file.
