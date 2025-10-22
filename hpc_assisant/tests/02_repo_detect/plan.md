# Execution plan – Suite 02_repo_detect

## Goal
Ensure the agent can clone a repository into an isolated workspace and analyze its contents to infer the build system and language hints.

## Tests included
1. **T-0201-git-clone**
   - **Input**: repository descriptor in `data/repo_target.json`; scratch path instructions in `data/scratch_notes.md`.
   - **Steps**:
     1. Prepare the scratch directory (create, ensure clean state).
     2. Clone the repository using allow-listed commands.
     3. Capture the resulting commit SHA with `git rev-parse HEAD`.
     4. Save metadata to `runs/<timestamp>/repo.json`.
   - **Done when**:
     - Scratch directory contains the cloned repository.
     - Metadata file matches the structure in `expected/repo_metadata_template.json`.
     - Audit log records clone duration and exit code.

2. **T-0202-detect-buildsystem**
   - **Input**: cloned repository path from T-0201; detection checklist in `data/build_indicators.md`.
   - **Steps**:
     1. Scan for canonical files (`CMakeLists.txt`, `Makefile`, etc.).
     2. Identify primary languages based on file extensions.
     3. Populate `runs/<timestamp>/detection.json`.
   - **Done when**:
     - Detected build system matches the expected entry in `expected/detection.json`.
     - Language hints include at least one language with a percentage estimate.
     - Any ambiguity is noted under a `notes` field.

## Promotion to utils/
- **utils/repo**
  - `clone(url, ref, dest)` – returns `{ "path": "...", "sha": "..." }`.
  - `detect_buildsystem(path)` – returns `{ "type": "cmake|make|unknown", "languages": [...], "evidence": [...] }`.

Promote once tests pass and documentation explains:
- How scratch paths are chosen and cleaned.
- Handling of shallow clones vs full clones.
- Detection heuristics and thresholds for language percentages.
