# Execution plan – Suite 07_error_triage_link

## Goal
Provide deterministic classifications for link-time failures and actionable remediation steps.

## Tests included
1. **T-0701-undefined-reference**
   - **Input**: linker log in `data/undefined_reference.log`.
   - **Steps**:
     1. Run the triage routine with the provided log.
     2. Save the structured output to `runs/<timestamp>/triage/T-0701-undefined-reference.json`.
     3. Confirm the advice suggests linking the appropriate library or target.
   - **Done when**:
     - Output matches `expected/undefined_reference.json`.
     - Advice enumerates candidate libraries and `target_link_libraries` adjustments.
     - Confidence meets thresholds from suite 06.

2. **T-0702-ld-cannot-find**
   - **Input**: log in `data/ld_cannot_find.log`.
   - **Steps**:
     1. Execute triage and store results under `runs/<timestamp>/triage/T-0702-ld-cannot-find.json`.
     2. Ensure advice covers library path additions and module loads.
   - **Done when**:
     - Output matches `expected/ld_cannot_find.json`.
     - Advice lists `-L` path suggestions and relevant modules.
     - Audit log records the missing library name.

## Promotion to utils/
- **utils/triage** (link rules)
  - Extend `classify` to cover `link.undefined_reference` and `link.missing_library` rules.
  - Document priority relative to compile rules.
  - Ensure outputs include fields `missing_symbols`, `suggested_libraries`, or `library_name` where applicable.

Promote once both tests pass and documentation outlines:
- Regex coverage for multiple symbols in one log.
- Handling of C++ mangled names (trim to human-readable suggestion).
- Logging schema for triage decisions (hashes, truncated snippets).
