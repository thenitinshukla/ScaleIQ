# HPC Agent Assistant Overview

This project sketches an on-prem, privacy-first agent that helps HPC users build, diagnose, and launch workloads while keeping every action auditable and reproducible.

## Non-Negotiable Objectives
- **Local-first privacy**: models, indices, and logs stay on the service node; nothing leaves the cluster boundary.
- **HPC robustness**: understands Lmod/Environment Modules, Spack/Conda stacks, vendor toolchains (GCC, Clang, Intel, NVHPC, Cray), MPI flavors (OpenMPI, MVAPICH, IntelMPI), accelerators (CUDA, ROCm), OpenMP, and Apptainer images.
- **Reproducibility**: explicit plans, structured logs, generated `sbatch` scripts, and declarative environment descriptions.
- **Guided self-healing**: parses error output, suggests safe fixes, and retries without destructive side effects.
- **Auditability**: every move persists the tuple input → action → output inside versioned run logs.

## Macro-Architecture
- **Orchestrator LLM (local)**: a code-centric base model (StarCoder, CodeLlama, DeepSeek-Coder, Qwen3.5) drives planning and delegates to deterministic tools via function-calling.
- **Deterministic tool suite**:
  - `RepoManager`: clone repositories, checkout refs, and apply patches.
  - `ContextBuilder`: detect languages, build systems (CMake, Make, Bazel), and dependency manifests (`requirements.txt`, `spack.yaml`, `environment.yml`).
  - `EnvManager`: manage module loads, Spack/Conda environments, and critical path variables (`PATH`, `LD_LIBRARY_PATH`, `CPATH`, `PKG_CONFIG_PATH`).
  - `Builder`: configure and compile while capturing stderr and build artifacts.
  - `ErrorTriage`: classify failures and surface remediation tactics.
  - `JobPlanner`: emit partition-aware `sbatch`/`srun` plans for CPUs and GPUs.
  - `JobRunner`: submit, monitor (`squeue`, `sacct`), and gather logs.
  - `Containerizer` (optional): produce Apptainer recipes or Spack buildcache entries.
  - `KB/RAG`: index local documentation (center wiki, Leonardo guides, READMEs, known-error logs) with FAISS.
- **Isolated executor**: operates inside user sandboxes on `$SCRATCH`, performs dry-runs before destructive commands, and enforces an allow-list.
- **State storage**: each run persists JSON Lines events, stdout/stderr, commit hashes, and toolchain metadata under `runs/`.

## Operational Prompting
- **System prompt**: encodes agent role, HPC safety rules, and planner–executor workflow.
- **Context pack**: embeds project signature (languages, build system, dependencies), cluster policy (modules, partitions, limits), and compact session history.
- **Guidance excerpt**: “If unsure of the toolchain, present a plan with verifiable steps and a dry-run. Produce idempotent commands with `set -euo pipefail`. Prefer `module spider` for discovery. Default to `CMAKE_BUILD_TYPE=Release` unless overridden. Document assumptions.”

## Available Moves FSM
- Core states: `GATHER → PLAN_ENV → BUILD → TRIAGE → BUILD (loop) → PLAN_JOB → SUBMIT → MONITOR → COLLECT`.
- Transitions hinge on command outcomes plus confidence scores from the error parser, mirroring the “available moves” notebook.

## Technical Content Schema
- **Command catalog**: minimal command set with inline rationale.
- **Job options**: required vs optional fields (GPU count, nodes, memory, walltime).
- **Environment variables**: highlight keys needed for compilers, MPI, CUDA/ROCm.
- **Expected outputs**: binaries, libraries, structured logs.
- **Executable example**: reference build-and-run flow to validate the stack.
- **HPC specifics**: MPI nuances, GPU caveats, filesystem quotas, Slurm limits.
- **Failure notes**: catalog recurring errors with diagnostic steps.

## Error Parser Design
- **Categories**: configure, compile, link, runtime, Slurm submission/epilogue, MPI, CUDA/ROCm.
- **Pattern rules**:
  - `fatal error: mpi.h: No such file` → load MPI module or adjust include paths.
  - `undefined reference to ...` → add missing libraries to link line or `target_link_libraries`.
  - `nvcc fatal : Unsupported gpu architecture` → align `-gencode` flags or CUDA module version.
  - `ld: cannot find -l<lib>` → load the proper module or supply library paths.
- **Outputs**: each rule returns a diagnosis, candidate command, minimal patch suggestion, and rationale.

## Security and Policy Guardrails
- Allow-listed binaries only (git, cmake, make, gcc/clang/nvhpc, spack, conda, sbatch/srun, module, apptainer).
- Non-interactive execution with credential masking (e.g., git tokens).
- Respect storage constraints: use `$SCRATCH`, avoid filling `$HOME`.
- Every step emits JSON logs containing inputs, exit codes, stdout, and stderr.

## Minimal Python Prototype
- `hpc_agent.py` registers tools, lays out `ProjectSpec`, `BuildPlan`, and `JobSpec`, and demonstrates repository cloning, build detection, configuration/compilation, error triage, and `sbatch` rendering.
- Error triage uses regex-driven rules that annotate build failures without executing cluster commands.

## Job Planner Example
- `example_sbatch.py` shows how to materialize a version-controlled `job.sbatch` via `render_sbatch`, ensuring reproducible submissions for CPU or GPU partitions.

## Local RAG Strategy
- Ingest cluster-specific documentation, policies, project READMEs, and anonymized error logs.
- Index with FAISS and local embeddings (e.g., bge-base, e5, or the host model’s embedder).
- Retrieve fresh snippets before each move; cache frequent answers for known GPU tiers (A100 vs. MI250).

## Testing Strategy
- Unit tests for error parser rules, `sbatch` generator, and build-system detection.
- Golden runs against toy C/C++/CUDA/MPI projects with expected outputs.
- Negative cases that exercise missing headers, libraries, or mismatched GPU architectures.
- Dry-run wrappers for potentially destructive commands; lint checks to validate Slurm flags.

## Real-Cluster Integration Roadmap
- Tie into Lmod via `modulecmd python load …` so environment mutations persist in-process.
- Respect `spack.yaml` by running `spack concretize`, `spack env activate`, and `spack build`.
- Add Apptainer workflows for intractable toolchains.
- Inject local policy metadata (accounts, QoS, partition quotas, GPU/CPU limits) through RAG.
- Auto-detect GPU architecture via `nvidia-smi` / `rocm-smi` and map to correct compiler flags.

## Why This Design Works
- The LLM plans and delegates, letting deterministic tools provide transparency and determinism.
- All artifacts (commands, logs, `sbatch` scripts) remain inspectable and versionable.
- “Moves” remain extendable, enabling incremental capability growth without changing the orchestrator.
- Local models, open formats, and explicit run records avoid vendor lock-in.
