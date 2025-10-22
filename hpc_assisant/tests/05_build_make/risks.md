# Risks and mitigations – Suite 05_build_make

- **Missing make binary**
  - *Signal*: Command fails with `make: command not found`.
  - *Action*: Load the appropriate module (e.g., `gcc` or `build-tools`); confirm `which make` before running.

- **Incorrect working directory**
  - *Signal*: Make cannot find the `Makefile`.
  - *Action*: Ensure the build runs from the project root described in `data/project_layout.md`.

- **Over-aggressive parallelism**
  - *Signal*: Build fails with resource or locking errors when using high `-j` values.
  - *Action*: Follow the guidance in `data/parallelism.md`; retry with lower parallelism and log the adjustment.

- **Stale artifacts**
  - *Signal*: Build reuses outdated objects causing inconsistent results.
  - *Action*: Run `make clean` before the main target; document the clean step in the audit log.

- **Targets missing from manifest**
  - *Signal*: Expected binaries are absent or checksums diverge.
  - *Action*: Rebuild with verbose logging to identify compilation failures; update manifest only after verifying determinism.
