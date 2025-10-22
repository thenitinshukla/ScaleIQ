# Error triage utilities specification

## Purpose
Normalize build and link failure logs into structured diagnostics with reproducible advice.

## Responsibilities
- Apply ordered rule sets for compile, link, and GPU build errors using regex patterns.
- Compute confidence scores and include evidence snippets.
- Produce remediation advice referencing modules, flags, or commands.
- Redact sensitive paths before persisting outputs.

## Interface
```python
class ErrorTriage:
    def __init__(self, rules: list[Rule], redactors: list[Callable[[str], str]]): ...
    def classify(self, stderr: str) -> dict: ...
    def load_rules(self, suite: str | None = None) -> None: ...
```

### Rules
- `compile.missing_header` → trigger on `fatal error: <header>: No such file or directory`.
- `compile.invalid_flag` → trigger on `unknown argument` / `unrecognized option` lines.
- `link.undefined_reference` → trigger on `undefined reference to` patterns, capture symbol list.
- `link.missing_library` → trigger on `cannot find -l<lib>` or `library not found for -l<lib>`.
- `gpu.unsupported_architecture` → trigger on `nvcc fatal : Unsupported gpu architecture` messages and capture the requested architecture.
- `gpu.missing_offload_arch` → trigger on diagnostics requesting `--offload-arch` or similar HIP clang messages.

Each rule defines:
- `pattern`: compiled regex with named groups.
- `category`: `compile`, `link`, or `gpu`.
- `advice`: templated strings referencing modules, compiler/linker flags, or GPU architecture adjustments.
- `confidence`: base score with optional boosts when multiple matches occur.

## Outputs
Return dictionary with keys:
- `test_id` (optional), `category`, `rule_id`, `confidence`, `evidence`/`missing_symbols`/`library_name`, `advice` (list of strings).
- Optional `notes` for ambiguous cases.

## Logging
- Persist results to `runs/<timestamp>/triage/<case>.json`.
- Record original log SHA256 and redaction mask details in `events.jsonl`.
- Include rule ordering metadata for debugging (e.g., `evaluated_rules`).
