# Leonardo — CINECA HPC Documentation

## Table of Contents
- [Introduction](#introduction)
- [Access to the System](#access-to-the-system)
- [System Architecture](#system-architecture)
- [Hardware Details](#hardware-details)
  - [Booster Partition](#booster)
  - [DCGP Partition](#dcgp)
- [File Systems and Data Management](#file-systems-and-data-management)
- [Job Managing and Slurm Partitions](#job-managing-and-slurm-partitions)
  - [Booster Partitions](#booster-partitions)
  - [DCGP Partitions](#dcgp-partitions)
- [Network Architecture](#network-architecture)
  - [Booster Network](#booster-network)
  - [DCGP Network](#dcgp-network)
- [Advanced Information](#advanced-information)
- [Documents and References](#documents-and-references)

---

## Introduction

**Leonardo** is the pre-exascale Tier-0 supercomputer of the EuroHPC Joint Undertaking (JU), hosted by **CINECA** and located at the **Bologna DAMA-Technopole** in Italy.

This guide provides specific information about the Leonardo cluster, including details that differ from the general behavior described in the broader HPC Clusters section.

---

## Access to the System

Leonardo is accessible via **SSH** (Secure Shell) protocol at:

```
login.leonardo.cineca.it
```

The connection automatically redirects to one of the available login nodes. You can also connect directly to specific login endpoints:

```
login01-ext.leonardo.cineca.it
login02-ext.leonardo.cineca.it
login05-ext.leonardo.cineca.it
login07-ext.leonardo.cineca.it
```

> ⚠️ **Warning:** Access to Leonardo requires **two-factor authentication (2FA)**.  
> Refer to the [Access to the Systems](https://docs.hpc.cineca.it/general/access.html#access-to-the-systems) section for setup instructions.

---

## System Architecture

Leonardo, supplied by **EVIDEN ATOS**, is based on two compute blade types, available through distinct **Slurm partitions**:

| Blade Type | Description |
|-------------|--------------|
| **X2135 GPU blade** | Based on NVIDIA Ampere A100-64 accelerators — *Booster partition* |
| **X2140 CPU blade** | Based on Intel Sapphire Rapids processors — *Data Centric General Purpose (DCGP) partition* |

The system uses **NVIDIA Mellanox InfiniBand HDR (High Data Rate)** connectivity with in-network computing acceleration, ensuring ultra-low latency and high throughput.

- **Booster Partition:** pre-production in May 2023 → full production July 2023  
- **DCGP Partition:** pre-production in January 2024 → full production February 2024

---

## Hardware Details

### Booster

| Type | Specification |
|------|----------------|
| **Models** | Atos BullSequana X2135, Da Vinci single-node GPU |
| **Racks** | 116 |
| **Nodes** | 3456 |
| **Processors/node** | [Intel Xeon Platinum 8358 (48M Cache, 2.60 GHz)](https://www.intel.com/content/www/us/en/products/sku/212282/intel-xeon-platinum-8358-processor-48m-cache-2-60-ghz/specifications.html) |
| **CPU/node** | 32 |
| **Accelerators/node** | 4× [NVIDIA Ampere100 custom](https://doi.org/10.17815/jlsrf-8-186), 64 GiB HBM2e NVLink 3.0 (200 GB/s) |
| **Local Storage** | None |
| **RAM/node** | 512 GiB DDR4 3200 MHz |
| **Rmax** | 241.2 PFlop/s ([Top500 entry](https://www.top500.org/system/180128/)) |
| **Network** | 200 Gbps NVIDIA Mellanox HDR InfiniBand — Dragonfly+ Topology |
| **Storage** | 106 PiB HDD (Capacity Tier) + 5.7 PiB SSD (Fast Tier) |

---

### DCGP

| Type | Specification |
|------|----------------|
| **Models** | Atos BullSequana X2140 three-node CPU blade |
| **Racks** | 22 |
| **Nodes** | 1536 |
| **Processors/node** | [Intel Xeon Platinum 8480+ (105M Cache, 2.00 GHz)](https://www.intel.com/content/www/us/en/products/sku/231746/intel-xeon-platinum-8480-processor-105m-cache-2-00-ghz/specifications.html) |
| **CPU/node** | 112 cores/node |
| **Accelerators** | None |
| **Local Storage** | 3 TiB |
| **RAM/node** | 512 GiB DDR5 4800 MHz |
| **Rmax** | 7.84 PFlop/s ([Top500 entry](https://www.top500.org/system/180204/)) |
| **Network** | 200 Gbps NVIDIA Mellanox HDR InfiniBand — Dragonfly+ Topology |
| **Storage** | 106 PiB HDD (Capacity Tier) + 5.7 PiB SSD (Fast Tier) |

---

## File Systems and Data Management

Leonardo follows the general CINECA file system organization. For global details, see [File Systems and Data Management](https://docs.hpc.cineca.it/hpc/hpc_data_storage.html#file-systems-and-data-management).  
Differences specific to Leonardo include handling of **$TMPDIR** on various nodes:

- **Login nodes:** `/scratch_local` (14 TB shared area). No quotas; files must be manually cleaned.  
- **Serial node (lrd_all_serial):** local 14 TB SSD, managed via Slurm `job_container/tmpfs` plugin.  
  - Request via: `--gres=tmpfs:XX` (max 1 TB). Default `/tmp` = 10 GB.  
- **DCGP nodes:** local 3 TB SSD, same plugin management. Request via `--gres=tmpfs:XX`.  
  - Note: requested `gres/tmpfs` contributes to billing.  
- **Booster nodes:** RAM-based `/tmp` (10 GB fixed). `gres/tmpfs` not available.

---

## Job Managing and Slurm Partitions

See also [Scheduler and Job Submission](https://docs.hpc.cineca.it/hpc/hpc_scheduler.html#scheduler-and-job-submission).

### Booster Partitions

| Partition | QOS | Cores/GPUs per Job | Walltime | Max per User | Priority | Notes |
|------------|-----|--------------------|-----------|---------------|-----------|--------|
| `lrd_all_serial` *(default)* | normal | 4 cores (8 logical) | 04:00:00 | 1 node / 4 cores | 40 | No GPUs; budget-free |
| `boost_usr_prod` | normal | 64 nodes | 24:00:00 | — | 40 | — |
| `boost_qos_dbg` | — | 2 nodes | 00:30:00 | 2 nodes / 64 cores / 8 GPUs | 80 | Debug |
| `boost_qos_bprod` | — | 65–256 nodes | 24:00:00 | 256 nodes | 60 | — |
| `boost_qos_lprod` | — | 8 nodes | 4-00:00:00 | 8 nodes / 32 GPUs | 40 | Max per project account |
| `boost_fua_dbg` | normal | 2 nodes | 00:10:00 | 2 nodes / 64 cores / 8 GPUs | 40 | EUROfusion only |
| `boost_fua_prod` | normal | 16 nodes | 24:00:00 | 4 jobs per user (max 32 nodes) | 40 | EUROfusion only |

> **Note:** *boost_fua_dbg* and *boost_fua_prod* are exclusive to **EUROfusion** users.

---

### DCGP Partitions

| Partition | QOS | Cores per Job | Walltime | Max per User | Priority | Notes |
|------------|-----|---------------|-----------|---------------|-----------|--------|
| `lrd_all_serial` *(default)* | normal | max 4 cores (8 logical) | 04:00:00 | 1 node / 4 cores | 40 | Budget-free |
| `dcgp_usr_prod` | normal | 16 nodes | 24:00:00 | 512 nodes/project | 40 | — |
| `dcgp_qos_dbg` | — | 2 nodes | 00:30:00 | 2 nodes / 224 cores | 80 | Debug |
| `dcgp_qos_bprod` | — | 17–128 nodes | 24:00:00 | 512 nodes/project | 60 | Min 17 nodes |
| `dcgp_qos_lprod` | — | 3 nodes | 4-00:00:00 | 3 nodes / 336 cores | 40 | Long jobs |
| `dcgp_fua_dbg` | normal | 2 nodes | 00:10:00 | 2 nodes / 224 cores | 40 | EUROfusion only |
| `dcgp_fua_prod` | normal | 16 nodes | 24:00:00 | — | 40 | EUROfusion only |

---

## Network Architecture

Leonardo employs a **state-of-the-art InfiniBand HDR (200 Gbps)** network with **Dragonfly+ topology**, built using [NVIDIA Quantum QM8700 Smart Switches](https://nvdam.widen.net/s/zmbw7rdjml/infiniband-qm8700-datasheet-us-nvidia-1746790-r12-web).

### Key Features
- **Hierarchical cell structure** for modular scalability.  
- **Inter-cell all-to-all connectivity** with 18 links per pair of cells.  
- **Intra-cell non-blocking two-layer fat-tree topology.**  
- **Adaptive routing** for congestion avoidance.  
- **Dedicated partitions:** 19 Booster cells, 2 DCGP cells, 1 hybrid cell, 1 management cell.

#### Booster Network

- 6 × Atos BullSequana XH2000 racks per cell  
- 3 × L2 switches, 3 × L1 switches per rack  
- 30 compute nodes (4 GPUs each)

**L2 Switches**
- UP: 22 × 200 Gbps ports to other cells  
- DOWN: 18 × 200 Gbps ports to L1 switches  
- Oversubscription: 0.8 : 1

**L1 Switches**
- UP: 18 × 200 Gbps ports to L2 switches  
- DOWN: 40 × 100 Gbps ports to GPUs  
- Oversubscription: 1.11 : 1

#### DCGP Network

- 8 × Atos BullSequana XH2000 racks per cell  
- 18 L2 switches, 16 L1 switches, 624 compute nodes

**L2 Switches**
- UP: 22 × 200 Gbps ports to other cells  
- DOWN: 18 × 200 Gbps ports to L1 switches  
- Oversubscription: 0.8 : 1

**L1 Switches**
- 9 switches × 40 downlinks → Oversubscription 1.11 : 1  
- 9 switches × 38 downlinks → Oversubscription 1.05 : 1

---

## Advanced Information

**Network Topology Map:** [Download ntopology.dat](https://docs.hpc.cineca.it/_downloads/b3e4d490b726ab3df2335843480b2537/ntopology.dat)  
**Distance Matrix (bz2):** [Download distance matrix](https://docs.hpc.cineca.it/_downloads/958475284937277d554ff9cb0fcdca7b/ntopology-dst_mtx.tar.bz2)

### Distance metric values:
| Value | Meaning |
|--------|----------|
| 0 | Same node |
| 1 | Same L1 switch, same cell |
| 2 | Different L1 switch, same cell |
| 3 | Different L1 switch and cell |

**Switch Naming Format:**
```
isw<RRrrSS>
```
- RR = region number  
- rr = rack number  
- SS = switch ID (even = L1, odd = L2)

---

## Documents and References

- **Main publication:**  
  *CINECA Supercomputing Centre, SuperComputing Applications and Innovation Department.*  
  (2024). “LEONARDO: A Pan-European Pre-Exascale Supercomputer for HPC and AI applications.”  
  *Journal of Large-Scale Research Facilities, 8*, A186.  
  DOI: [10.17815/jlsrf-8-186](https://doi.org/10.17815/jlsrf-8-186)

- **Intel Xeon Witley platform:**  
  [Third Generation Xeon Scalable Family Overview](https://software.intel.com/content/www/us/en/develop/articles/third-generation-xeon-scalable-family-overview.html)

- **Performance Tuning Guides:**  
  [Intel Xeon Performance Tuning and Solution Guides](https://software.intel.com/content/www/us/en/develop/articles/xeon-performance-tuning-and-solution-guides.html)

- **Additional PDFs:**  
  - [Tuning Guide (PDF)](https://docs.hpc.cineca.it/_downloads/5a3e534740b0c9c9ee5fec0649ba4230/Tuning_guide.pdf)  
  - [Deep Learning Guide (PDF)](https://docs.hpc.cineca.it/_downloads/29dbbb88e01d5ab22853da137556bb11/Deep_learning.pdf)

---
© 2025 CINECA User Support Team  
Built with [Sphinx](https://www.sphinx-doc.org/) using [ReadTheDocs theme](https://github.com/readthedocs/sphinx_rtd_theme)
