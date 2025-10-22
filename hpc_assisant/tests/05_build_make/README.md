# Suite 05 – Make build

This suite validates classic Makefile workflows to ensure the agent can drive GNU Make builds and capture reproducible logs and artifacts.

## Suite contents
- **T-0501-make-j** – Run `make -j` (or `make -jN`) on a toy project, verify targets are produced, and archive build logs and timing data.

## Shared prerequisites
- POSIX toolchain with `make` available (module guidance from suites 03 and 04 applies).
- Sample Make project prepared according to `data/project_layout.md`.
- Writable run workspace for build outputs and logs.

## High-level manual procedure
1. Stage the Make project in the run workspace per `plan.md`.
2. Execute the build command specified in `data/make_command.txt`.
3. Capture logs, timings, and artifact manifests under `runs/<timestamp>/make_build/`.
4. Compare outputs with the expectations recorded in `expected/`.

## Supporting documentation
- `plan.md` defines the step-by-step process and promotion criteria for `utils/build_make`.
- `data/` provides project structure notes, command templates, and parallelism guidelines.
- `expected/` lists the required log format, artifact manifest, and metrics templates.
- `risks.md` covers common Make-related failures and mitigations.
