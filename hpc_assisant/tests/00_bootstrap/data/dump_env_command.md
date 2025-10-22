# Environment dump instructions

1. Open an allow-listed shell and move to the project root.
2. Load `.env`:
   ```bash
   set -a
   source .env
   set +a
   ```
3. Export the environment to JSON while masking sensitive fields:
   ```bash
   env | sort | python scripts/mask_env.py > runs/<timestamp>/env.json
   ```
   - If `scripts/mask_env.py` is unavailable, follow the alternative described in `expected/env_redaction_rules.md`.
4. Record the outcome in the audit stream (`runs/<timestamp>/events.jsonl`) including the command, exit code, and SHA256 hash of the generated file.
