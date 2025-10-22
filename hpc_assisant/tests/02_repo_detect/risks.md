# Risks and mitigations – Suite 02_repo_detect

- **Network unavailability**
  - *Signal*: Clone command fails with DNS or timeout errors.
  - *Action*: Switch to the local mirror described in `data/repo_target.json`; verify allow-listed commands are used.

- **Dirty scratch directory**
  - *Signal*: Pre-existing files interfere with the clone.
  - *Action*: Clean or recreate the scratch path before each run; document cleanup steps in audit logs.

- **Ambiguous build-system detection**
  - *Signal*: Both `CMakeLists.txt` and `Makefile` are present without clear priority.
  - *Action*: Record multiple evidences and note precedence rules in `utils/repo`.

- **Missing language hints**
  - *Signal*: Detection output lacks language percentages.
  - *Action*: Ensure file scanning covers relevant extensions; include fallback heuristics.

- **Repository drift**
  - *Signal*: Commit SHA differs between runs, causing expectation mismatch.
  - *Action*: Pin a specific ref in `data/repo_target.json` and include it in the metadata template.
