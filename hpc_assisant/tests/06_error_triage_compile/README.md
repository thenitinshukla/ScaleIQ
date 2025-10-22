# Suite 06 – Compile error triage

This suite defines how the agent classifies compilation failures and suggests safe remediations.

## Suite contents
- **T-0601-missing-header** – Detect `fatal error: mpi.h: No such file` and recommend loading the appropriate MPI module.
- **T-0602-invalid-flag** – Detect unknown compiler options and suggest removing or correcting the flag.

## Shared prerequisites
- Access to sample build logs provided in `data/`.
- Familiarity with the regex-based triage rules promoted to `utils/triage`.
- Audit logging ready to store triage decisions under `runs/<timestamp>/triage/`.

## High-level manual procedure
1. Ingest the failing build log from `data/` following `plan.md`.
2. Run the classification workflow, producing structured output in `runs/<timestamp>/triage/<case>.json`.
3. Compare the results with `expected/` to confirm category, rule ID, advice, and confidence.

## Supporting documentation
- `plan.md` enumerates the triage steps and promotion criteria.
- `data/` contains log snippets that trigger each rule.
- `expected/` includes the canonical JSON outputs for each case.
- `risks.md` explains common pitfalls such as overlapping regex matches or missing advice.
