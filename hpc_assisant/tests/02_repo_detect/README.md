# Suite 02 – Repository detection

This suite validates cloning capabilities and build-system detection for target repositories.

## Suite contents
- **T-0201-git-clone** – Clone a sample repository into a scratch workspace and record the commit SHA.
- **T-0202-detect-buildsystem** – Inspect the cloned tree for build-system indicators (CMake, Make) and report the dominant language hints.

## Shared prerequisites
- Network or local mirror access to the sample repository defined in `data/repo_target.json`.
- Writable scratch space (e.g., `$SCRATCH/tmp`) that respects the allow list.
- Logging enabled under `runs/<timestamp>/repo.json`.

## High-level manual procedure
1. Execute the clone instructions described in `plan.md` using the URL in `data/repo_target.json`.
2. Record clone metadata (URL, ref, commit SHA, timestamp) to `runs/<timestamp>/repo.json`.
3. Run build-system detection on the cloned directory and compare the outcome with `expected/detection.json`.

## Supporting documentation
- `plan.md` lists the step-by-step execution flow and promotion criteria for `utils/repo`.
- `data/` holds repository references and command templates.
- `expected/` contains the detection output template and example metadata.
- `risks.md` covers common issues such as missing network access or ambiguous detection results.
