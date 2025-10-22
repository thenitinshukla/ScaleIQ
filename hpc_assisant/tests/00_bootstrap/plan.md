# Execution plan – Suite 00_bootstrap

## Goal
Demonstrate that the agent can load configuration from `.env`, mask secrets, and create the minimal repository layout before other suites start.

## Tests included
1. **T-0001-env-file**
   - **Input**: actual `.env` file; checklist `data/env_keys_checklist.md`.
   - **Steps**:
     1. Export environment variables (`set -a; source .env; set +a` or equivalent).
     2. Follow `data/dump_env_command.md` to serialize the environment into `runs/<timestamp>/env.json`.
     3. Mask sensitive values as specified in `expected/env_redaction_rules.md`.
   - **Done when**:
     - `runs/<timestamp>/env.json` exists and contains all required keys.
     - Sensitive values show the `***MASKED***` pattern.
     - An audit log entry is recorded in `runs/<timestamp>/events.jsonl` with status `success`.

2. **T-0002-layout**
   - **Input**: target structure described in `expected/layout_tree.txt`.
   - **Steps**:
     1. Create (or verify) directories `runs/`, `tests/`, `utils/`.
     2. Place placeholder files (`runs/.keep`, minimal `utils/README.md`) following the checklist.
     3. Update the project README to reflect the current structure.
   - **Done when**:
     - `find` reports a structure matching `expected/layout_tree.txt`.
     - Directories have owner `rwx` permissions and expose no secrets.
     - The root README documents the foundational folders.

## Promotion to utils/
- **utils/config** – Document the `ConfigProvider` interface (sources: `.env`, environment overrides, validation rules).
- **utils/paths** – Define `RunPaths` to create per-run folders with references to `env.json`, `events.jsonl`, and `report.md`.

Promote once both tests pass and the documentation covers:
- Configuration sources and precedence.
- Masking rules for sensitive variables.
- Naming convention for runs (`YYYYMMDD-HHMMSS` or similar) and expected artifact layout.
