# Leonardo Cluster Snapshot

- Login nodes provide internet access; compute/GPU partitions do not.
- Use reconnaissance commands (`pwd`, `ls`, `module avail`, environment listings) to understand your session before making changes.
- `sbatch --test-only` is required for dry-run validation from the login node.
- Keep artefacts under `/leonardo/home/userexternal/<uid>/` and consult `sinfo` to identify appropriate partitions.
