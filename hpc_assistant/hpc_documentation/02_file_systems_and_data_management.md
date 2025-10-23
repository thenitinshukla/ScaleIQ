# File Systems and Data Management — CINECA HPC Documentation

All HPC systems at **CINECA** share a consistent logical disk structure based on the **Lustre** filesystem. This section provides an overview of available storage areas, best practices for Lustre, data management tools, and transfer mechanisms.

---

## Overview of File Systems

CINECA HPC systems define multiple storage areas depending on data type and retention policy.

| Name | Attributes | Quota | Backup | Notes |
|------|-------------|--------|---------|--------|
| `$HOME` | Permanent, user-specific | 50 GB | Daily | Default user home area |
| `$WORK` | Permanent, shared | 1 TB | No | Shared with project collaborators |
| `$FAST` | Permanent, shared (Leonardo only) | 1 TB | No | High I/O performance area |
| `$SCRATCH` | Temporary, user-specific | - / 20 TB | No | Files older than 40 days deleted |
| `$TMPDIR` | Temporary, user-specific | Dynamic | No | Removed at job completion |
| `$PUBLIC` | Permanent, open (Leonardo only) | 50 GB | No | Accessible to all cluster users |
| `$DRES` | Permanent, shared | Defined by project | No | Cross-platform and inter-project repository |

> **Note**: Always use environment variables (e.g., `$HOME`, `$WORK`) instead of absolute paths in scripts.

> **Warning**: Misuse of `$SCRATCH` (e.g., extending file lifetime via `touch`) may result in restrictions or bans.

---

## Storage Area Details

### `$HOME` — Permanent, User-Specific

- Default area after login.  
- Stores user configurations and small datasets.  
- Backed up daily (max 3 versions).  
- Retention: data persist while account is active.

### `$WORK` — Permanent, Shared per Project

- Main collaborative working area.  
- Retained for 6 months after project completion.  
- No backup; suitable for large data I/O.  
- Default quota: 1 TB (extendable).  
- All project members can write; permissions managed by `chmod`.  
- Manage multiple `$WORK` areas using `chprj`.

### `$FAST` — High-Performance I/O (Leonardo Only)

- Shared per project; retained 6 months post-project.  
- No backup; optimized for I/O-intensive workloads.  
- Fixed quota: 1 TB.  
- Ideal for data requiring fast read/write operations.

### `$SCRATCH` — Temporary User-Specific

- Local scratch area for batch jobs.  
- Files deleted after 40 days of inactivity.  
- No quota, but monitored for ethical use.  
- Use `chmod` to modify file access.  
- Daily log (`CLEAN_<YYYYMMDD>.log`) tracks deletions.

### `$TMPDIR` — Job-Specific Temporary Storage

- Defined per compute node.  
- On Leonardo: `/tmp`, visible via `df -h /tmp`.  
- Removed automatically at job end.  
- Use `$TMPDIR` within job scripts for local I/O speedup.

### `$PUBLIC` — Permanent, Open, User-Specific (Leonardo)

- 50 GB per user.  
- Accessible to all cluster users.  
- No backup; persists for account lifetime.

### `$DRES` — Shared Repository (Cross-Project)

- Must be requested explicitly.  
- Retained for 6 months after DRES completion.  
- Types:  
  - **FS**: High-throughput disks (login nodes only)  
  - **ARCH**: Magnetic tape via LTSFS  
  - **REPO**: iRODS-based repository  
- Default: public read-only; customizable permissions.

---

## Backup Policy and Data Availability

- Daily backups apply **only to `$HOME`** (max 3 copies).  
- Deleted files retained for 2 months.  
- Project data available for 6 months post-expiration.  
- Users are responsible for backing up critical data.

![Backup Timeline](https://docs.hpc.cineca.it/_images/file_time.png)

> **Important:** Data availability beyond 6 months after project end is **not guaranteed**.

---

## Lustre Filesystem Best Practices

Lustre is optimized for **large files** and **parallel I/O**. Performance can degrade with small files or excessive metadata operations.

### Key Recommendations

1. **Minimize metadata operations** (`ls`, `find`, `du`, `df`).  
   Use Lustre tools like `lfs find` instead.
2. **Avoid wildcards** (`*`, `?`) on large directories.  
   Use precompiled file lists instead.
3. **Organize files** into subdirectories to prevent contention.  
   Example: 90,000 files → 300 dirs × 300 files.
4. **Avoid small files**; aggregate using `tar`, `HDF5`, or `NetCDF`.
5. **Minimize repeated operations**; buffer writes where possible.
6. **Prevent contention**; avoid concurrent writes to same file region.

---

## File Striping and PFL (Parallel File Layouts)

Striping enhances parallel performance by spreading files across **Object Storage Targets (OSTs)**.

### Parameters

- **Stripe Count**: number of OSTs (1 = single OST).  
- **Stripe Size**: amount written before moving to next OST (default ~1MB).

### Leonardo Defaults

| Filesystem | File Size Range | Stripe Count | Stripe Size |
|-------------|----------------|---------------|--------------|
| `$HOME` | 64 KB – 10 GB / >10 GB | 1 / 4 | 1 MB |
| `$WORK`, `$FAST`, `$SCRATCH` | 64 KB – 10 GB / 10–100 GB / >100 GB | 1 / 2 / 4 | 1 MB |
| `$PUBLIC` | 64 KB – 10 GB / >10 GB | 1 / 4 | 1 MB |

> Lustre incrementally applies PFL rules as file size grows.

### Stripe Management Commands

```bash
# Set stripe count
lfs setstripe -c 2 mydir

# Set stripe count and size
lfs setstripe -c 4 -S 4M hugefile

# Check file stripe info
lfs getstripe largefile.txt
```

---

## Data Occupancy Monitoring

CINECA provides two tools for monitoring storage usage:

### `cindata`
Displays detailed usage per filesystem area.

```bash
$ cindata
USER    AREA           USED   QUOTA   USED%
myuser  /gpfs/work/... 114G   30T     48.8%
myuser  /gpfs/scratch/ 149G   420T    81.2%
```

### `cinQuota`
Summarizes disk usage with quotas and file counts.

```bash
$ cinQuota
Filesystem                        used    quota  files
/g100/home/userexternal/myuser00   22.6G   50G   194295
/g100_scratch/userexternal/myuser00 1.95T   -     41139
```

---

## Managing File Permissions

Default `$WORK` / `$DRES` permissions:
- Owner: `rwx`
- Group: `rwx`
- Other: `-`

Change directory access:
```bash
chmod 755 mydir
chmod 777 shared_dir
```

Switch `$WORK` project target:
```bash
chprj -l      # list all projects
chprj -d <account_no>  # switch project
```

---

## Data Transfer Methods

### Data Movers

Use **datamover nodes** for high-volume transfers (no CPU time limits).

**Leonardo Datamovers:**  
`data.leonardo.cineca.it` → nodes: `dmover1`–`dmover4`

**Authentication:**
- `publickey`: via 2FA SSH certificate.  
- `hostbased`: available when connected from a CINECA login node.

**Available tools:** `scp`, `rsync`, `sftp`, `wget`, `curl`, `rclone`, `aws s3`, `s3`.

Example (Leonardo):  
```bash
rsync -PravzHS myfile user@data.leonardo.cineca.it:/gpfs/work/project/
```

### GridFTP Transfers

For high-performance inter-cluster transfers using `globus-url-copy`:

```bash
globus-url-copy -vb -cd   sshftp://user@gftp.g100.cineca.it:22/path/from/   sshftp://user@gftp.leonardo.cineca.it:22/path/to/
```

- Uses ports **20000–25000**.  
- Supports restartable, parallel, and secure transfers.

---

## Endianness

All CINECA clusters use **little-endian** architecture.

---

© 2025 CINECA User Support Team  
Documentation built with [Sphinx](https://www.sphinx-doc.org) and [Read the Docs Theme](https://readthedocs.org).
