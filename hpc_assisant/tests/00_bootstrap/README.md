# Suite 00 – Bootstrap

This suite makes sure the agent starts from a clean, minimal baseline: variables from `.env` must reach child processes and the repository layout must match the Master Test Plan.

## Suite contents
- **T-0001-env-file** – Verifies that `.env` is loaded and that masked values are captured under `runs/<timestamp>/env.json`.
- **T-0002-layout** – Confirms the foundational directories (`runs/`, `utils/`, `tests/`) and placeholder files exist with correct permissions.

## Shared prerequisites
- `.env` file at the project root (or as defined by the Master Test Plan) containing at least `VLLM_API_BASE`, `VLLM_API_KEY`, `VLLM_MODEL_NAME`, and `VLLM_EMBEDDING_MODEL`.
- Access to an allow-listed shell environment (e.g., `bash`, `jq`, `python`, `env`).
- Write permissions in `runs/` to capture configuration logs.

## High-level manual procedure
1. **Load configuration** – Source `.env` in the reference shell and generate an environment log following the instructions in `plan.md`.
2. **Validate masking** – Review `runs/<timestamp>/env.json` to ensure required keys are present and sensitive values (tokens, keys) are masked.
3. **Validate repository layout** – Compare the actual directory structure against `expected/layout_tree.txt`, checking for `.keep` files and updated README entries.

## Supporting documentation
- `plan.md` describes the deliverables to promote into `utils/config` and `utils/paths`.
- `data/` provides shell preparation materials and variable checklists.
- `expected/` collects sample logs and the desired layout.
- `risks.md` lists common failure modes (missing `.env`, permission issues, writes outside the allow list) with mitigations.
