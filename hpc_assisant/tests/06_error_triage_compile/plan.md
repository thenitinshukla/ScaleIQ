# Execution plan – Suite 06_error_triage_compile

## Goal
Establish deterministic rules for classifying compilation errors and producing actionable remediation guidance.

## Tests included
1. **T-0601-missing-header**
   - **Input**: compiler log snippet in `data/missing_header.log`.
   - **Steps**:
     1. Feed the log into the triage routine.
     2. Capture the structured output as `runs/<timestamp>/triage/T-0601-missing-header.json`.
     3. Verify category, rule ID, confidence, and advice fields.
   - **Done when**:
     - Output matches `expected/missing_header.json`.
     - Advice lists module load suggestions and include path hints.
     - Audit log records the rule applied and regex match snippet.

2. **T-0602-invalid-flag**
   - **Input**: log snippet in `data/invalid_flag.log`.
   - **Steps**:
     1. Execute triage on the log.
     2. Store the result under `runs/<timestamp>/triage/T-0602-invalid-flag.json`.
     3. Confirm the advice recommends removing or replacing the offending flag.
   - **Done when**:
     - Output matches `expected/invalid_flag.json`.
     - Confidence exceeds the threshold defined in `expected/triage_thresholds.md`.
     - There is an audit entry showing the offending flag.

## Promotion to utils/
- **utils/triage** (compile rules)
  - `classify(stderr: str) -> dict`
  - Document rule IDs (e.g., `compile.missing_header`, `compile.invalid_flag`).
  - Provide advice templates referencing module loads and command adjustments.

Promote once both tests pass and documentation covers:
- Regex patterns and how they avoid false positives.
- Confidence score calculation.
- Logging format for triage decisions (including hashes of source logs).
