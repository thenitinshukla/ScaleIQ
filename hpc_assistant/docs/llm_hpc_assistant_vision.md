# HPC LLM Assistant – Product Vision

## 1. Mission statement
Design and ship an LLM-first assistant (“HPC Codex”) that can take full ownership of a user’s workload on an on-premise HPC cluster (e.g., Leonardo @ Cineca). The assistant plans, executes, monitors, and reports every action required to deliver the requested result. Traditional scripts, CLI wrappers, or rule-based agents become subordinate tools: the LLM reasons about what to do, issues commands, receives observations, and iterates until completion or user stop.

## 2. Core capabilities
1. **Repository intake** – Clone user-provided source (git URL or local path), inspect project metadata, and summarise findings (languages, build system, entrypoints, docs).
2. **Environment reasoning** – Understand the target cluster (hardware, modules, queues, policy). Decide which modules, compilers, MPI/toolchains, and environment managers (Spack, Conda, virtualenv) are required.
3. **Build & dependency orchestration** – Configure, compile, or otherwise prepare the project. Handle fallbacks (alternate compilers, flags), install missing packages, and ensure reproducibility.
4. **Adaptive error triage** – When commands fail (configure/compile/link/runtime/Slurm), classify the failure, surface log evidence, propose the minimal safe fix, and retry.
5. **Job planning & execution** – Generate Slurm sbatch/srun commands tailored to hardware availability (CPU/GPU/MPI), optimise resource requests, submit jobs, monitor state, and collect outputs.
6. **Performance-aware adjustments** – When project requirements are underspecified, choose reasonable defaults (e.g., detect accelerator availability, enable mixed precision, adjust `--gpus`/`--ntasks`).
7. **User-facing telemetry** – Stream actions, rationales, and logs back to the user. Support pause/resume, context injection, and manual overrides.
8. **Audit & reproducibility** – Log every (prompt → decision → command → outcome) tuple, store artefacts, hash configs, and produce end-of-run reports with next-step recommendations.

## 3. Safety & policy constraints
- Operate entirely inside the HPC environment; never reach the public internet.
- Respect cluster policy: partitions, QoS, account usage, module allow-list, storage quotas.
- Command allow-list enforcement (git, cmake, make, gcc/clang/nvhpc, spack, conda/mamba, module, sbatch/srun, apptainer, nvidia-smi/rocm-smi, safe `python`, etc.).
- Automatic dry-run or guardrails before executing potentially destructive operations; log the rationale.
- Configurable redaction for secrets (tokens, credentials) in reports/logs.

## 4. Interaction model
1. **Input** – User submits instruction plus optional repo URL/path and desired outcome.
2. **Context pack assembly** – Runtime layer injects machine info, policy, project metadata, prior logs, and relevant HPC documentation snippets (see §6).
3. **LLM reasoning loop**
   - Produce PLAN, preview commands, or tool-call requests.
   - Python runner executes tool-calls, returns observations (stdout/stderr, exit codes).
   - LLM updates PLAN, applies fixes, or asks for clarification.
4. **Completion** – LLM emits a structured REPORT covering build artefacts, job outputs, timing, and suggested improvements.

## 5. Execution lifecycle
| Phase | LLM responsibilities | Tooling responsibilities |
| --- | --- | --- |
| Context acquisition | Explain understanding, request missing info | Provide machine/project context from cache/HPC docs |
| Planning | Output numbered plan, risk annotations | None (passive) |
| Action | Emit preview/tool-call JSON | Runner validates command, executes, streams observation |
| Error handling | Classify failure, cite log line, propose minimal fix | Provide truncated logs, confirm fix attempts |
| Job launch | Produce sbatch/srun script with explanation | Runner writes file, optionally dry-runs, submits when safe |
| Monitoring | Decide polling cadence, interpret state | Runner executes `squeue/sacct`, returns JSON timeline |
| Reporting | Summarise outcomes, metrics, next steps | Assemble artefacts (events.jsonl, logs, sbatch) |

## 6. Knowledge integration
- Leverage `hpc_documentation/` Markdown files: module usage, compiler quirks, Slurm examples, best practices. Index them for retrieval (future RAG layer).
- Encourage LLM to cite doc sections when recommending modules or flags.
- Maintain a prompt registry (system + context templates) for different HPC sites.

## 7. Artefact management
- Directory structure under `/runs/<timestamp>/` with `events.jsonl`, `llm_request.json`, `tool_call.json`, `sbatch/`, `logs/`, `report.md`.
- Append-only event log with timestamps, tool, action, status, hashes of stdout/stderr.
- End-of-run dataset for reproducibility (compressed archive, optional).

## 8. Testing approach
- Keep automated tests under `tests/` but exclude from git by default (guarded via `.gitignore`).
- Tests exercise the orchestration (request construction, sanitisation, tool-call parsing) using fixtures before hitting live clusters.
- Higher-level integration tests can replay command/observation transcripts.

## 9. Roadmap (draft)
1. Finalise system prompt + context schema.
2. Build LangChain/sglang runner that enforces `/nothink`, strips `<think>`.
3. Recreate core suites (LLM I/O, repo intake, build planner, Slurm planner) in the new workflow.
4. Wire command execution through allow-listed wrappers with safety checks.
5. Integrate HPC documentation via retrieval (phase 2).
6. Harden logging/reporting; support pause/resume and manual overrides.
7. Deploy on Leonardo staging nodes; iterate with real user projects.

---
This document captures the target behaviour and responsibilities of the LLM-driven HPC assistant. Update it as the architecture evolves or new cluster requirements emerge.
