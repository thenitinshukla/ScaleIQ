# Suite 07 – Link error triage

This suite codifies the detection and remediation of linker errors, focusing on missing symbols and libraries.

## Suite contents
- **T-0701-undefined-reference** – Identify "undefined reference" messages and suggest linking the correct library or target.
- **T-0702-ld-cannot-find** – Detect `ld: cannot find -l<lib>` errors and recommend module loads or library path adjustments.

## Shared prerequisites
- Sample linker logs under `data/`.
- Awareness of the rule set defined in `utils/triage` for link errors.
- Run workspace ready to store triage outputs in `runs/<timestamp>/triage/`.

## High-level manual procedure
1. Load the failing linker output from `data/` as described in `plan.md`.
2. Apply the triage routine, generating JSON summaries per case.
3. Validate that the outputs match the expectations in `expected/`.

## Supporting documentation
- `plan.md` details the sequence for each test and promotion criteria.
- `data/` provides log snippets that trigger linker rules.
- `expected/` includes canonical triage outputs for each scenario.
- `risks.md` outlines pitfalls like duplicate symbol matches or ambiguous library names.
