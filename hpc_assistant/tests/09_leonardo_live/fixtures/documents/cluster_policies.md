# Leonardo Cluster Policies

- Login nodes have internet access; compute nodes (including GPU nodes) **do not**.
- Use reconnaissance commands (`pwd`, `ls`, `module avail`, `conda env list`) at the start of every session to understand the environment before mutating it.
- Use `module avail <name>` to inspect available modules, then `module load <name>` to enable them.
- Batch submissions must use `sbatch --test-only` during dry-runs from the login node.
- Keep source code, build artefacts, and scratch data under `/leonardo/home/userexternal/<uid>/`.
- Use `sinfo` to discover valid GPU partitions (e.g., `boost_usr_prod`); `compute` is CPU-only and offers no internet access.
