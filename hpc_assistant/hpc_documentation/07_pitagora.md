# Pitagora — CINECA HPC Documentation

## Overview

**Pitagora** is the new EUROfusion supercomputer hosted by CINECA and currently built in the CINECA’s headquarters in Casalecchio di Reno, Bologna, Italy.  
The cluster is supplied by **Lenovo Corporation** and is composed of two partitions:
- A general-purpose **CPU-based** partition named **DCGP (Data Centric General Purpose)**.
- An accelerated partition based on **NVIDIA H100 accelerators**, named **Booster**.

This guide contains specific information that differs from the general behavior described in the [HPC Clusters](https://docs.hpc.cineca.it/hpc/hpc_clusters.html) documentation.

---

## Access to the System

The system is reachable via **SSH (Secure Shell)** at:

```
login.pitagora.cineca.it
```

Connections are automatically established to one of the available login nodes.  
Alternatively, users can connect to specific login nodes:

```
login01-ext.pitagora.cineca.it
login02-ext.pitagora.cineca.it
login03-ext.pitagora.cineca.it
login04-ext.pitagora.cineca.it
login05-ext.pitagora.cineca.it
login06-ext.pitagora.cineca.it
```

> ⚠️ **Warning**  
> Access to Pitagora requires **two-factor authentication (2FA)**.  
> More details are available in [Access to the Systems](https://docs.hpc.cineca.it/general/access.html#access-to-the-systems).

> 📝 **Note**  
> Even-numbered login nodes share the same architecture as the Booster partition compute nodes,  
> while odd-numbered ones share the same architecture as the DCGP partition compute nodes.  
>
> - `login-boost.pitagora.cineca.it` → connects to one of the **even-numbered** login nodes (Booster type).  
> - `login-dcgp.pitagora.cineca.it` → connects to one of the **odd-numbered** login nodes (DCGP type).

---

## System Architecture

The Pitagora cluster, supplied by **Lenovo**, is based on two compute blade types available through two distinct **SLURM partitions**:

- **GPU blade** based on *NVIDIA H100 accelerators* → **Booster partition**  
- **CPU-only blade** based on *AMD Turin 128-core processors* → **DCGP partition**

The overall system architecture uses **NVIDIA Mellanox InfiniBand HDR (High Data Rate)** interconnect with **smart in-network computing acceleration engines**, ensuring extremely low latency and high throughput for HPC and AI workloads.

---

## Hardware Details

### Booster Partition

| Type | Specific |
|------|-----------|
| **Models** | Lenovo SD650-N V3 |
| **Racks** | 7 |
| **Nodes** | 168 |
| **Processors/node** | 2 × Intel Emerald Rapids 6548Y (32 cores @ 2.4 GHz) |
| **CPU/node** | 64 cores |
| **Accelerators/node** | 4 × NVIDIA H100 SXM (80 GB HBM2e) |
| **Local Storage/node (tmfs)** | 2 × 7.68 GiB SSDs (HW RAID 1) |
| **RAM/node** | 512 GiB DDR5 @ 5600 MHz |
| **Rmax** | 27.27 PFlop/s ([TOP500](https://www.top500.org/system/180348/)) |
| **Internal Network** | NVIDIA ConnectX-7 NDR200 |
| **Storage (raw capacity)** | 2 × 7.68 GiB SSDs (HW RAID 1) |

---

### DCGP Partition

| Type | Specific |
|------|-----------|
| **Models** | Lenovo SD665 V3 |
| **Racks** | 14 |
| **Nodes** | 1008 |
| **Processors/node** | 2 × AMD Turin 128-core (Zen 5 @ 2.4 GHz) |
| **CPU/node** | 256 cores |
| **Accelerators/node** | None |
| **Local Storage/node (tmfs)** | Diskless |
| **RAM/node** | 768 GiB DDR5 @ 6400 MHz |
| **Rmax** | 17 PFlop/s ([TOP500](https://www.top500.org/system/180348/)) |
| **Internal Network** | NVIDIA ConnectX-7 NDR SharedIO 200 Gbit/s |
| **Storage (raw capacity)** | Diskless nodes |

---

## Job Managing and SLURM Partitions

The following tables describe the **SLURM partitions** for both Booster and DCGP environments.  
Please note that **SLURM email service** is currently **disabled**.

For general information about job submission and scheduling, see  
[Scheduler and Job Submission](https://docs.hpc.cineca.it/hpc/hpc_scheduler.html#scheduler-and-job-submission).

---

### Booster Partitions

| Partition | QOS | # Nodes / per job | Walltime | # Max Nodes / per user | Priority | Notes |
|------------|-----|------------------|-----------|-------------------------|-----------|-------|
| **boost_fua_prod** | normal | max = 16 | 24:00:00 | 32 | 40 | — |
| **boost_qos_fuabprod** | min = 17 (full nodes)<br>max = 32 | 24:00:00 | 32 | 60 | Runs on 96 nodes (GrpTRES) |
| **boost_fua_dbg** | normal | max = 2 | 00:30:00 | 2 | 40 | Runs on 8 nodes (GrpTRES) |

---

### DCGP Partitions

| Partition | QOS | # Nodes / per job | Walltime | # Max Nodes / per user | Priority | Notes |
|------------|-----|------------------|-----------|-------------------------|-----------|-------|
| **dcgp_fua_prod** | normal | max = 64 | 24:00:00 | 64 | 40 | — |
| **dcgp_qos_fuabprod** | min = 65 (full nodes)<br>max = 128 | 24:00:00 | 128 | 60 | Runs on 640 nodes (GrpTRES) |
| **dcgp_qos_fualprod** | — | max = 3 | 4-00:00:00 | 3 | 40 | — |
| **dcgp_fua_dbg** | normal | max = 2 | 00:30:00 | 2 | 40 | Runs on 8 nodes (GrpTRES) |

---

## Processes / Threads Binding and Affinity

### Process Binding

By default, `srun` (the SLURM launcher) performs **automatic binding**.  
For multi-threaded applications, request the appropriate number of CPUs per task and bind the processes to cores:

```bash
srun --cpus-per-task=<n> --cpu-bind=cores
```

- OpenMPI (`mpirun`) binds processes **to cores by default**.  
  For multi-threaded applications, this can cause CPU overallocation.  
  Use the following to disable or adjust binding:

```bash
mpirun --bind-to none
```

or bind to multiple cores with:

```bash
mpirun --map-by socket:PE=$SLURM_CPUS_PER_NODE
```

- IntelMPI (`mpirun` with Hydra process manager) performs **correct binding** by default.  
  If using IntelMPI, **unset** the `I_MPI_PMI_LIBRARY` variable (set automatically when loading the module) to suppress verbose warnings:

```bash
unset I_MPI_PMI_LIBRARY
```

---

### Thread Affinity

All available compilers (**gcc**, **nvhpc**, **aocc**, **intel**) **do not bind threads to cores by default**.  
You can control thread affinity using OpenMP environment variables:

```bash
export OMP_PLACES=cores
export OMP_PROC_BIND=close
```

These control how threads are placed and bound across cores for optimal performance.

---

© 2025 CINECA User Support Team  
Built with [Sphinx](https://www.sphinx-doc.org/) using the [Read the Docs theme](https://github.com/readthedocs/sphinx_rtd_theme).
