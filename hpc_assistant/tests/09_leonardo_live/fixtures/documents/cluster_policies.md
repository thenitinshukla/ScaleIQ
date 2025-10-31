# Leonardo Cluster Policies

- Login nodes have internet access; compute nodes (including GPU nodes) **do not**.
- Use `module spider <name>` to inspect available modules, then `module load <name>` to enable them.
- Batch submissions must use `sbatch --test-only` during dry-runs from the login node.
- Keep source code, build artefacts, and scratch data under `/leonardo/home/userexternal/<uid>/`.
- Use the `booster` partition for GPU workloads; `compute` is CPU-only.
