# Parallel build guidance

- Default to `--parallel $(nproc)` capped at 8.
- On shared login nodes, limit to 4 to avoid contention.
- Record the chosen parallelism in `runs/<timestamp>/cmake_build/metrics.json`.
