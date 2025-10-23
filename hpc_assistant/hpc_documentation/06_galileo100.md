# Galileo100 — CINECA HPC Documentation

## Overview

**Galileo100** is a high-performance computing (HPC) infrastructure co-funded by the European ICEI (Interactive Computing e-Infrastructure) project and engineered by DELL.  
It serves as the national Tier-1 system for scientific research and has been available to Italian public and industrial researchers since **September 2021**.  

The cluster also includes **77 cloud computing servers** and was expanded in **November 2022** with 82 additional nodes.  
It supports high-end technical and industrial HPC projects, as well as meteorology and environmental simulations.

This guide contains specific information about Galileo100 that differs from the general HPC cluster documentation.

---

## Access to the System

Galileo100 is accessible via **SSH (Secure Shell)** at the following hostname:

```
login.g100.cineca.it
```

The connection is automatically redirected to one of the available login nodes.  
You may also connect directly to specific login hosts:

```
login01-ext.g100.cineca.it
login02-ext.g100.cineca.it
login03-ext.g100.cineca.it
```

> **Warning:**  
> Access to Galileo100 requires **two-factor authentication (2FA)**.  
> For setup details, see [Access to the Systems](https://docs.hpc.cineca.it/general/access.html#access-to-the-systems).

---

## System Architecture

### Hardware Details

| **Type** | **Specification** |
|-----------|-------------------|
| Models | Dual-socket Dell PowerEdge |
| Nodes | 630 |
| Processors per node | 2 × Intel Xeon Platinum 8276/L @ 2.4GHz |
| CPU per node | 48 |
| Accelerators per node | 2 × NVIDIA V100 PCIe3 GPUs (32 GB) on 36 Viz nodes |
| RAM per node | 384 GiB (+ 3.0 TiB Optane on 180 fat nodes) |
| Peak Performance | 2 PFlop/s (3.53 TFlop/s per single node) |
| Internal Network | Mellanox Infiniband 100GbE |

---

## Disks and Filesystems

Galileo100 follows the general **CINECA storage organization**.  
See [File Systems and Data Management](https://docs.hpc.cineca.it/hpc/hpc_data_storage.html#file-systems-and-data-management) for standard reference.  

Only cluster-specific differences are noted here.

---

## Job Managing and SLURM Partitions

| **Partition** | **QOS** | **#Cores per Job** | **Walltime** | **Max Jobs / Resources per User** | **Max Memory per Node (MB)** | **Priority** | **Notes** |
|----------------|----------|--------------------|--------------|----------------------------------|------------------------------|---------------|------------|
| g100_all_serial (default) | noQOS | 4 cores | 04:00:00 | 4 cores / 120 submitted jobs | 31,200 (30 GB) | 40 | on two login nodes; budget free |
| g100_all_serial (default) | qos_install | 16 cores | 04:00:00 | 16 cores / 1 running job | 100 GB | 40 | request to [superc@cineca.it](mailto:superc@cineca.it) |
| g100_usr_dbg | noQOS | 2 nodes | 01:00:00 | — | 375,300 (366 GB) | 40 | — |
| g100_usr_dbg | qos_ind | Depending on agreement | Depending on agreement | — | 375,300 (366 GB) | 90 | Partition dedicated to specific user agreements |
| g100_usr_prod / g100_usr_smem / g100_usr_pmem | noQOS | min = 1, max = 32 nodes | 24:00:00 | 100 running / 120 submitted jobs | 375,300 (366 GB) | 40 | thin + persistent memory nodes; thin-only or persistent-only |
| g100_usr_prod / g100_usr_smem / g100_usr_pmem | g100_qos_bprod | min = 1537 (33 nodes), max = 3072 (64 nodes) | 24:00:00 | 100 running / 120 submitted jobs | 375,300 (366 GB) | 60 | thin + persistent memory nodes; thin-only or persistent-only |
| g100_usr_prod / g100_usr_smem / g100_usr_pmem | g100_qos_lprod | min = 1, max = 2 nodes | 4-00:00:00 | 2 nodes / 100 running / 120 submitted jobs | 375,300 (366 GB) | 40 | thin + persistent memory nodes; thin-only or persistent-only |
| g100_usr_prod / g100_usr_smem / g100_usr_pmem | qos_special | >32 nodes | >24:00:00 | — | 375,300 (366 GB) | 40 | request to [superc@cineca.it](mailto:superc@cineca.it) |
| g100_usr_bmem | noQOS | 25 nodes | 24:00:00 | 100 running / 120 submitted jobs | 3,036,000 (3 TB) | 40 | runs on fat nodes |
| g100_usr_interactive | noQOS | max = 0.5 node | 8:00:00 | 100 running / 120 submitted jobs | 375,300 (366 GB) | 40 | on GPU nodes — use `--gres=gpu:N (N=1)` |
| g100_meteo_prod | qos_meteo | — | 24:00:00 | — | 375,300 (366 GB) | 40 | Partition reserved for meteorological services; not open for production |

---

## Dedicated Services

### Interactive Computing

Galileo100 provides browser-based access via **JupyterLab**:

🔗 [https://jupyter.g100.cineca.it/](https://jupyter.g100.cineca.it/)

This allows users to run jobs interactively through a web interface.  
For additional configuration and usage details, refer to [Interactive Computing](https://docs.hpc.cineca.it/services/interactive_computing.html#interactive-computing).

> **Note:**  
> This service is currently **in pre-production**, meaning usage is **not charged** to the project budget and is provided **without warranty**.

---

**Previous:** [Leonardo](https://docs.hpc.cineca.it/hpc/leonardo.html)  
**Next:** [Pitagora](https://docs.hpc.cineca.it/hpc/pitagora.html)

© Copyright 2025, CINECA User Support Team.  
Built with [Sphinx](https://www.sphinx-doc.org/) using the [Read the Docs](https://readthedocs.org/) theme.
