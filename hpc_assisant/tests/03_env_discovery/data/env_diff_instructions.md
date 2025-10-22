# Environment diff instructions

1. Before loading modules, capture the baseline:
   ```bash
   env | sort > runs/<timestamp>/env_before.txt
   ```
2. Execute the load sequence in `module_load_sequence.sh`.
3. After loading, capture the updated environment:
   ```bash
   env | sort > runs/<timestamp>/env_after.txt
   ```
4. Compute the diff (example using Python):
   ```bash
   python scripts/env_diff.py runs/<timestamp>/env_before.txt runs/<timestamp>/env_after.txt > runs/<timestamp>/env_delta.json
   ```
5. Confirm the delta highlights modified keys (`PATH`, `LD_LIBRARY_PATH`, compiler-specific variables).
6. Log the command sequence and diff summary to `runs/<timestamp>/events.jsonl`.
