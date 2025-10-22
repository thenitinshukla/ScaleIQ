# MPI utilities specification

## Purpose
Assist with compiling and running MPI workloads under Slurm, providing command composition helpers.

## Responsibilities
- Generate `mpirun`/`srun` commands based on resource requests.
- Capture module/environment requirements for MPI jobs.
- Parse runtime output to verify rank mapping.

## Interface
```python
class MPIHelper:
    def compose_mpirun(self, ntasks: int, env: dict | None = None) -> list[str]: ...
    def parse_output(self, stdout: str) -> dict: ...
```

### `compose_mpirun`
- Uses parameters from `tests/19_mpi_job/data/run_params.json`.
- Returns command segments (e.g., `["srun", "--ntasks=4", "--nodes=2"]`).

### `parse_output`
- Validates output similar to `tests/19_mpi_job/expected/hello_output.txt`.
- Extracts rank/node mapping for logging.

## Logging
- Record compiled command, modules loaded, and execution summary in audit log.
