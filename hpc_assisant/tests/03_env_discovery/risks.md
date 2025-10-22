# Risks and mitigations – Suite 03_env_discovery

- **Module subsystem unavailable**
  - *Signal*: `module` command not found or returns initialization errors.
  - *Action*: Source the cluster-provided initialization script (usually `/etc/profile.d/modules.sh`); document the requirement in `data/env_diff_instructions.md`.

- **Parsing drift**
  - *Signal*: Structured JSON lacks expected keys because `module spider` output changed.
  - *Action*: Update parsing rules to accommodate new formats; include regression samples in `expected/modules_template.json`.

- **Environment contamination**
  - *Signal*: Loaded modules affect unrelated tests or persist beyond cleanup.
  - *Action*: Record all loaded modules and unload them during teardown; consider `module purge` with caution.

- **Child process isolation failure**
  - *Signal*: `which` commands invoked as children cannot locate the expected binaries.
  - *Action*: Verify module loads are executed via `modulecmd` in-process; ensure environment variables are exported before spawning children.

- **Unsupported shells**
  - *Signal*: Scripts run under shells without module integration (e.g., minimal `/bin/sh`).
  - *Action*: Force execution under Bash or Zsh per cluster guidance; document compatibility in `plan.md`.
