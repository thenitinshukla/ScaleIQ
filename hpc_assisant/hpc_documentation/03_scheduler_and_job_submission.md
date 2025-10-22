# Scheduler and Job Submission

CINECA HPC clusters are accessed via dedicated login nodes, designed for tasks like environment setup, data transfer, and light pre/post-processing. Computational workloads must be submitted to compute nodes through the **Slurm** scheduler, ensuring fair resource allocation.

## Overview of SLURM

Slurm (Simple Linux Utility for Resource Management) is an open-source job scheduler and resource manager with three core functions:

1. **Resource Allocation:** Assigns compute nodes for user jobs.
2. **Job Execution:** Provides the framework for starting, executing, and monitoring jobs.
3. **Queue Management:** Handles job queues and prioritization.

Two primary execution modes are available:

- **Batch Mode:** For production workloads, where users prepare a job script and submit it using `sbatch`.
- **Interactive Mode:** For testing and debugging, with temporary resource allocation via `salloc` or `srun`.

> **Note:** Interactive use on compute nodes is only permitted via SLURM. Login nodes are restricted to short, lightweight operations (≤10 minutes CPU time).

---

## Basic Usage of SLURM

### Job Lifecycle

1. Create a job script.
2. Submit using `sbatch`.
3. Monitor with `squeue`, `sinfo`, or `scontrol`.
4. Cancel with `scancel` if necessary.

### Example Job Script

```bash
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --time=1:00:00
#SBATCH --error=myJob.err
#SBATCH --output=myJob.out
#SBATCH --account=<Project Account>
#SBATCH --partition=<partition_name>
#SBATCH --qos=<qos_name>

./my_application
```

### Common SLURM Directives

| Directive | Description | Example |
|------------|--------------|----------|
| `--job-name` | Job name | `#SBATCH --job-name=my_job` |
| `--output` | Output file | `#SBATCH --output=output.log` |
| `--error` | Error file | `#SBATCH --error=error.log` |
| `--time` | Time limit | `#SBATCH --time=01:00:00` |
| `--partition` | Partition (queue) | `#SBATCH --partition=compute` |
| `--ntasks` | Number of tasks | `#SBATCH --ntasks=1` |
| `--cpus-per-task` | CPUs per task | `#SBATCH --cpus-per-task=4` |
| `--mem` | Memory per node | `#SBATCH --mem=8GB` |
| `--gres` | Generic resources (e.g. GPUs) | `#SBATCH --gres=gpu:1` |
| `--qos` | Quality of Service | `#SBATCH --qos=<qos_name>` |
| `--account` | Project Account | `#SBATCH --account=<account_no>` |

---

## Example Job Scripts

### Serial Job

```bash
#!/bin/bash
#SBATCH --job-name=serial_job
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=<partition_name>
#SBATCH --qos=<qos_name>
#SBATCH --mem=2G
#SBATCH --output=serialJob.out
#SBATCH --account=<project_account>

./my_serial_app
```

### OpenMP Job

```bash
#!/bin/bash
#SBATCH --job-name=openmp_job
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48
#SBATCH --partition=<partition_name>
#SBATCH --mem=128G
#SBATCH --output=myJob.out
#SBATCH --account=<project_account>

module load intel
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

srun ./my_openmp_app < input > output
```

### MPI Job

```bash
#!/bin/bash
#SBATCH --time=01:00:00
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --partition=<partition_name>
#SBATCH --qos=<qos_name>
#SBATCH --account=<project_account>

module load intel intelmpi
srun my_mpi_program < input > output
```

### GPU Job

```bash
#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --time=04:00:00
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=10
#SBATCH --gres=gpu:4
#SBATCH --partition=<gpu_partition>
#SBATCH --qos=<qos_name>
#SBATCH --account=<project_account>

module load cuda/12.2 openmpi
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

srun --mpi=pmix ./my_distributed_gpu_app --config config.yaml
```

---

## Interactive Job Submission

### Using `salloc`

Allocates compute resources interactively, allowing real-time commands within the reserved environment.

```bash
salloc -N 1 --ntasks-per-node=8
srun hostname   # Runs on compute node
exit            # Ends session
```

You can also run scripts directly:

```bash
salloc -N 1 --ntasks=8 ./myscript.sh
```

### Using `srun --pty`

Starts an interactive shell directly on the compute node:

```bash
srun -N 1 --ntasks-per-node=8 --pty /bin/bash
```

Use `--overlap` if multiple `srun` commands will be launched inside the same session.

---

## Monitoring and Managing Jobs

### `squeue`

Displays job queue status.

```bash
squeue -u $USER
squeue -j 123456
squeue -p gpu
```

Example formatted output:

```bash
squeue -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
```

### `sinfo`

Shows the status of partitions and nodes.

```bash
sinfo -o "%P %D %t %C"
```

### `scontrol`

Used for querying and modifying SLURM job details.

```bash
scontrol show job 123456
scontrol hold <job_id>
scontrol release <job_id>
```

### `scancel`

Cancels jobs.

```bash
scancel 123456       # Cancel specific job
scancel -u $USER     # Cancel all jobs for user
scancel -p gpu -t PD # Cancel all pending GPU jobs
```

> **Note:** Users may only cancel their own jobs. Use caution with bulk cancellations.

---

© 2025 CINECA User Support Team
