# Risks and mitigations – Suite 07_error_triage_link

- **Multiple undefined symbols**
  - *Signal*: Log lists many `undefined reference` lines for different symbols.
  - *Action*: Aggregate symbols in the triage output and prioritise advice covering all affected libraries.

- **Ambiguous library suggestions**
  - *Signal*: Several libraries could satisfy the missing symbol.
  - *Action*: Provide ranked suggestions and note manual verification steps.

- **False positives from warnings**
  - *Signal*: Linker warnings resemble errors (e.g., "undefined reference" in quotes).
  - *Action*: Ensure regexes anchor on fatal error lines and exit codes.

- **Missing module guidance**
  - *Signal*: Advice does not include module loads when required.
  - *Action*: Extend rule metadata with module hints drawn from site policy.

- **Redaction gaps**
  - *Signal*: Paths in logs reveal user directories or build caches.
  - *Action*: Apply the same redaction filters as compile triage before persisting outputs.
