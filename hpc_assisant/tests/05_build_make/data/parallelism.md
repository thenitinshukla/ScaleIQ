# Parallelism guidance

- Use `-j$(nproc)` capped at 4 on login nodes.
- For compute nodes, cap at 16 unless otherwise specified.
- Document the final `-j` value in `make_build/metrics.json`.
