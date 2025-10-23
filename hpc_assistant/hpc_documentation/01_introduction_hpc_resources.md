# Introduction to HPC Resources

This section provides an overview of **HPC Resources** and the essential characteristics of CINECA’s high-performance computing infrastructure.  
It introduces the CINECA clusters, the management of computational resources, and the budgeting and accounting rules applied to HPC projects.

---

## Budget and Accounting

The **`saldo`** command allows users to quickly retrieve information about their **Project Account**, including:
- Available budget,
- Usage by each associated user,
- Account expiration dates.

You can simply execute the command without options to view general information.

---

### 1. User Account Balance

To list all **Project Accounts** associated with your username:

```bash
saldo -b <User Account>
```

For clusters with multiple independent partitions (like **Leonardo**):

```bash
saldo -b        # Default: Booster partition
saldo -b --dcgp # For DCGP partition
```

**Example Output:**

```
-----------------------------------------------------------------------------------------------------------------------------------
account  start     end       total   localCluster  totConsumed  totConsumed%  monthTotal  monthConsumed (local h)
-----------------------------------------------------------------------------------------------------------------------------------
Proj_A   20110323  20300323  50000   25000         55027726     50.0          600         600
Proj_B   20220427  20301231 100000   10000         27086        10.0          731         731
Proj_C   20230524  20300323   6500       0             0         0.0            0           0
```

**Column description:**

| Column | Meaning |
|--------|----------|
| **Account** | Name of the Project Account (approved grant) |
| **Start Date / End Date** | Validity period of the grant |
| **Total Hours (local)** | Total CPU hours allocated on the local cluster |
| **Consumed (local)** | CPU hours used from that allocation |
| **Total Consumed (%)** | Percentage of total hours used |
| **Month Total** | Allocated hours for the current month |
| **Month Consumed** | Hours consumed this month |

---

### 2. Project Account Balance

To check the daily usage of a **Project Account** and see which users consumed resources:

```bash
saldo -a <Project Account>
```

**Example Output:**

```
------------------Resources used from 202404 to 202412------------------
date       username  account   localCluster  num.jobs   Consumed/h
--------------------------------------------------------------------
20240907   user001   example   5553:34:39    542
20240908   user001   example   22340:07:36   2676
20240909   user001   example   1606:21:39    154
20240910   user001   example   3210:42:40    285
--------------------------------------------------------------------
```

This report specifies:
- The date,
- Usernames associated with the project,
- Number of jobs submitted that day,
- Total hours consumed.

---

## Billing Policy

The **Billing Policy** defines how computational resource usage is converted into **budget consumption**.  
Understanding it is crucial for planning workloads efficiently and preventing unnecessary losses.

Budget consumption is measured in **effective CPU hours (CPUh)** and depends on:
- Number of nodes reserved,
- Resources allocated per node,
- Duration of job execution.

---

### Formula for Billed Hours

\[
BH = T \times N \times R \times C
\]

Where:

| Symbol | Meaning |
|---------|----------|
| **T** | Elapsed time (in hours) |
| **N** | Number of nodes allocated |
| **R** | Fraction of node resources reserved |
| **C** | Number of CPUs per node (depends on architecture) |

The **R factor** measures how much of a node’s total resources your job makes unavailable to others.  
It is defined as:

\[
R = \max_{r \in RES} \left( \frac{\text{Allocated}(r)}{\text{Total}(r)} \right)
\]

Typical resource types: CPU, GPU, RAM.

---

### Example

A job requests:

- 1 node  
- 4 CPUs  
- 4 GPUs  
- 3 hours walltime  

but runs for only 2 hours on the **Leonardo Booster** partition.

Given:
- T = 2h
- N = 1
- C = 32 (CPUs per Booster node)

We compute:
- 4/32 = 0.125 for CPU  
- 4/4 = 1.0 for GPU  

Hence R = 1.0

\[
BH = 2 \times 1 \times 1.0 \times 32 = 64\ CPUh
\]

➡️ The job consumes **64 effective CPU hours**.

---

### Notes

- The **serial partition** (for post-production and analysis) is *budget-free*.  
- Memory allocation per node is proportional to CPUs requested.  
- When a node is requested in **exclusive mode**, the entire node is billed regardless of used resources.  
- See **[Hardware Details](https://docs.hpc.cineca.it/hpc/leonardo.html#hardware-details)** for per-node specs.

---

## Budget Linearization

CINECA applies a **linearization policy** to balance scheduling priorities across projects.

Each **Project Account** has a **Monthly Quota (MQ)**:

\[
MQ = \frac{TB}{NM}
\]

Where:

| Symbol | Meaning |
|---------|----------|
| **TB** | Total assigned budget |
| **NM** | Number of months in project duration |

On the 1st of each month:
- Jobs run with **full priority** until the monthly quota is exhausted.
- Once MQ is depleted, jobs still run, but with **lower priority**.

This ensures fairness and efficient resource usage across all users.

**Best practice:**  
Distribute your workload linearly over the project duration.  
Bursting (non-linear usage) may reduce system responsiveness for all users.

![Budget Linearization](https://docs.hpc.cineca.it/_images/bud_lin.png)

---

## References
- [CINECA HPC Documentation – Introduction HPC Resources](https://docs.hpc.cineca.it/hpc/hpc_intro.html)
- Built with Sphinx using the ReadTheDocs theme.
