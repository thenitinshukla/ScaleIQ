# Risks and mitigations – Suite 00_bootstrap

- **Missing or incomplete `.env`**
  - *Signal*: T-0001 fails because some keys are not found.
  - *Action*: regenerate from `.env.example`; add the mandatory keys listed in `data/env_keys_checklist.md`.

- **Secrets exposed in cleartext**
  - *Signal*: `runs/<timestamp>/env.json` shows readable tokens.
  - *Action*: apply the masking rules in `expected/env_redaction_rules.md`; rerun the dump; confirm `utils/config` documents the masking behaviour.

- **Insufficient permissions on `runs/`**
  - *Signal*: unable to write `env.json` or `events.jsonl`.
  - *Action*: adjust permissions (`chmod 700 runs`) while preserving privacy; rerun the test.

- **Directories created outside the allow list**
  - *Signal*: T-0002 flags unexpected paths.
  - *Action*: relocate or remove extra directories; repeat the layout checklist.

- **Outdated root README**
  - *Signal*: manual review finds missing documentation for the foundational folders.
  - *Action*: update the “Repository structure” section to include `runs/`, `tests/`, and `utils/`.
