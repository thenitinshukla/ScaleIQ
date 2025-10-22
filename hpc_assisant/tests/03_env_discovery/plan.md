# Execution plan – Suite 03_env_discovery

## Goal
Validate that module discovery works with Lmod and that environment mutations persist across child processes launched by the agent.

## Tests included
1. **T-0301-module-spider**
   - **Input**: module families listed in `data/modules_target.md`; parsing hints in `data/spider_parsing_notes.md`.
   - **Steps**:
     1. Run `module spider <name>` for each target family.
     2. Normalize the output into structured JSON.
     3. Store the snapshot in `runs/<timestamp>/modules.json`.
   - **Done when**:
     - Snapshot includes at least three families (compiler, MPI, tooling) with available versions.
     - Output matches the shape defined in `expected/modules_template.json`.
     - Audit log records command invocations and parsing summary.

2. **T-0302-module-load-propagation**
   - **Input**: modules defined in `data/module_load_sequence.md`; environment diff helper in `data/env_diff_instructions.md`.
   - **Steps**:
     1. Capture baseline environment (`env` dump) before loading modules.
     2. Load modules using `modulecmd` or a sourced shell script.
     3. Launch a child command (`which gcc`, `which mpicc`) and capture its output.
     4. Compute environment delta and store it in `runs/<timestamp>/env_delta.json`.
   - **Done when**:
     - Delta highlights changes to `PATH`, `LD_LIBRARY_PATH`, and relevant variables.
     - Child command output reflects the loaded toolchain.
     - Results align with `expected/env_delta_template.json`.

## Promotion to utils/
- **utils/env**
  - `module_query(name)` – wraps `module spider` and returns structured data.
  - `module_load(sequence)` – applies module loads via `modulecmd` while capturing deltas.
  - `env_diff(before, after)` – computes key environment changes for auditing.

Promote once both tests pass and documentation covers:
- Shell compatibility requirements (Bash vs Zsh vs non-interactive shells).
- Strategies for persisting module state within long-lived agent processes.
- Handling of module load failures and rollback behaviour.
