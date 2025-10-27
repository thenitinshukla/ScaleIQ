# Leonardo dry-run fixture

This synthetic fixture mirrors the layout we expect on the Leonardo login node
when preparing a dry-run submission. The agent should:

- Inspect the repository (`git status`) and review available modules.
- Use `module spider` to confirm module availability.
- Keep all scheduler interactions in dry-run mode (`srun --test-only` or `sbatch --test-only`).
- Reference the provided `scripts/run_leonardo.sh` wrapper when planning the batch step.

Remember that the login node has internet access, while GPU nodes do not.
