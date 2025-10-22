# Suite 03 – Environment discovery

This suite verifies interactions with the cluster module system (Lmod/Environment Modules) and environment propagation to child processes.

## Suite contents
- **T-0301-module-spider** – Enumerate available modules and capture a snapshot of supported toolchains.
- **T-0302-module-load-propagation** – Load a selected set of modules and confirm PATH-related variables remain active for child processes.

## Shared prerequisites
- Lmod or Environment Modules available on the target cluster.
- Allow-listed commands (`module`, `env`, `python`) usable within the test shell.
- Access to a writable area for storing environment diffs (e.g., `runs/<timestamp>/env_delta.json`).

## High-level manual procedure
1. Execute the discovery instructions in `plan.md` to run `module spider` and parse the results into a structured snapshot.
2. Use the module list defined in `data/modules_target.md` to perform loads and launch a child process.
3. Compare the captured environment before and after loading modules against `expected/env_delta_template.json`.

## Supporting documentation
- `plan.md` details the step-by-step flow and promotion criteria for `utils/env`.
- `data/` provides target module families and helper commands for diffing environments.
- `expected/` includes templates for module snapshots and environment deltas.
- `risks.md` addresses common failure modes such as missing modules or shell incompatibilities.
