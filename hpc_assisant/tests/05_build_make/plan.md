# Execution plan – Suite 05_build_make

## Goal
Ensure the agent can build a Makefile project with controlled parallelism and produce reproducible logs and artifacts.

## Tests included
1. **T-0501-make-j**
   - **Input**: project description in `data/project_layout.md`; build command in `data/make_command.txt`; parallelism guidance in `data/parallelism.md`.
   - **Steps**:
     1. Stage the project in `runs/<timestamp>/workspace/make-toy/` from the source defined in suite 02.
     2. Run the make command with the recommended `-j` value.
     3. Capture stdout/stderr to `runs/<timestamp>/make_build/build.log`.
     4. Record timing, exit code, and generated targets.
     5. Produce an artifact manifest and checksums.
   - **Done when**:
     - Build exits with code 0.
     - Targets listed in `expected/artifact_manifest.json` exist with matching checksums.
     - Metrics file matches the structure in `expected/metrics_template.json`.
     - Audit log contains entries for command execution and artifact capture.

## Promotion to utils/
- **utils/build_make**
  - `run(path: Path, target: str | None = None, jobs: int | None = None) -> dict`
  - `collect_artifacts(path: Path, patterns: list[str]) -> list[dict]`

Promote once T-0501 passes and documentation explains:
- How `jobs` is selected based on `parallelism.md`.
- Handling of phony targets and incremental builds.
- Logging expectations: command invocation, duration, stdout/stderr summaries.
