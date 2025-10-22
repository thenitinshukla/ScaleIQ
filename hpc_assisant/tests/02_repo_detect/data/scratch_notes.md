# Scratch workspace notes

- Use `$SCRATCH/tmp/hpc-agent-tests` unless the cluster policy specifies another path.
- Ensure the directory is owned by the current user and has mode `700`.
- Remove previous clones before starting a new run.
- After successful detection, archive the workspace under `runs/<timestamp>/artifacts/clone.tar.gz` if retention is required.
