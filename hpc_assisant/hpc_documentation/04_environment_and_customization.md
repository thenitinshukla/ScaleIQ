# Environment and Customization — CINECA HPC Documentation

## Table of Contents
- [The Software Catalog](#the-software-catalog)
- [The module command](#the-module-command)
- [The modmap command](#the-modmap-command)
- [Compilers](#compilers)
  - [GCC](#gcc)
  - [NVIDIA nvhpc](#nvidia-nvhpc)
  - [Intel oneAPI](#intel-oneapi)
  - [AMD AOCC](#amd-aocc)
- [Basic MPI Execution](#basic-mpi-execution)
- [Totalview](#totalview)
- [Installing packages with Python environment](#installing-packages-with-python-environment)
- [SPACK](#spack)

---

## The Software Catalog

CINECA offers a variety of third-party applications and community codes that are installed on its HPC systems.
Most of the third-party software is installed using software modules mechanism (see [The module command](#the-module-command) section).
Information on the available packages and their detailed descriptions are organized in a catalog,
divided by discipline ([link](https://www.hpc.cineca.it/systems/software/)).

The catalog is also accessible directly on HPC clusters by using the commands `module` and `modmap` described in the next sections.

---

## The module command

All software installed on the CINECA clusters are available as modules. By default, a set of basic modules are preloaded in the environment at login.
To manage modules in the production environment, the user can execute the command `module` with a variety of options.

| Command | Action |
|----------|---------|
| `module avail` | show the available modules on the machine |
| `module load <appl>` | load the module in the current shell session, preparing the environment for the application |
| `module load autoload <appl>` | load the module and all dependencies in the current session |
| `module help <appl>` | show specific information and basic help on the application |
| `module list` | show the modules currently loaded in the shell session |
| `module purge` | unload all the loaded modules |
| `module unload <appl>` | unload a specific module |
| `module av -a` | show also the hidden modules available on the machine (usable but not guaranteed) |
| `module load <appl>/<version>` | to load a hidden module you must specify its version |

---

## The modmap command

For easy reading, the modules are collected in different profiles. Only the base profile is automatically loaded at login.
`modmap` is a very useful command to look for a specific module in all the profiles at once.
It shows in the standard output all the modules with the searched name and in which profile they can be found.

Example:

```bash
$ modmap -m lammps

Profile: archive
  applications lammps 20220623--openmpi--4.1.4--gcc--11.3.0-cuda-11.8
Profile: chem-phys
  applications lammps 29aug2024
  applications lammps 2aug2023
  applications lammps 2aug2023--intel-oneapi-compilers--2023.2.1
...
```

To load the module:

```bash
$ module load profile chem-phys
$ module load lammps/29aug2024
```

---

## Compilers

You can check the complete list of available compilers on a specific cluster with:

```bash
$ modmap -c compilers
```

### For GPU compilation (NVIDIA GPUs, cuda-aware)
- GNU Compilers Collection (GCC)
- NVIDIA nvhpc (ex PGI)
- NVIDIA cuda

### For CPU compilation
**Intel CPUs:**
- Intel oneAPI compilers (x and classic compilers)
- GNU Compilers Collection (GCC)

**AMD CPUs:**
- AOCC compilers
- GNU Compilers Collection (GCC)

---

## GCC

### Serial Compilation

The GNU compilers are always available. A GCC version is available on the system without needing to load any module.

```bash
$ modmap -m gcc
$ module load gcc/<version>
```

**Compiler commands:**
- `gfortran`: Fortran 95 compiler (includes legacy F77 support)
- `gcc`: C compiler
- `g++`: C++ compiler

**Environment variables set by the module:**
- `CC`: gcc
- `CXX`: g++
- `FC`: gfortran
- `F90`: gfortran
- `F77`: gfortran

**Documentation:**
```bash
$ module load gcc/<version>
$ man gcc
```

On accelerated clusters, GCC modules support device offloading (e.g., NVIDIA GPUs → nvptx).

### MPI Wrappers

The GCC OpenMPI implementation is available on all clusters.

```bash
$ module load openmpi/<version>
$ mpicc -o myexec myprog.c
```

---

## NVIDIA nvhpc

(ex PGI + NVIDIA CUDA)

### Serial Compilation

```bash
$ modmap -m nvhpc
$ module load nvhpc/<version>
$ man nvc
```

**Compilers included:**
- `nvc`, `nvc++`, `nvfortran`, `nvcc`
- Legacy PGI equivalents: `pgcc`, `pgc++`, `pgfortran`

**Main flags:**
- `-cuda` → enable CUDA linking (replaces -Mcuda)
- `-gpu` → control target accelerator regions
- `-acc` → enable OpenACC
- `-mp` → enable OpenMP (use `-mp=gpu` for GPU offload)

### MPI Wrappers

```bash
$ module load openmpi/<version>  # or hpcx-mpi/<version>
$ mpicc -o myexec myprog.c
```

---

## Intel oneAPI

### Serial Compilation

```bash
$ modmap -m intel-oneapi-compilers
$ module load intel-oneapi-compilers/<version>
```

**Compilers available:**
- **Classic:** `icc`, `icpc`, `ifort`
- **oneAPI (LLVM-based):** `icx`, `icpx`, `ifx`, `dpcpp`

From 2024+, only oneAPI compilers and `ifort` remain.  
From 2025, only oneAPI compilers are available.

```bash
$ ifx -o myexec myprog.f90
```

### MPI Wrappers

```bash
$ module load intel-oneapi-mpi/<version>
$ mpiicx -o myexec myprog.c
```

Wrappers available:
- **oneAPI:** `mpiicx`, `mpiicpx`, `mpiifx`
- **Classic:** `mpiicc`, `mpiicpc`, `mpiifort`

---

## AMD AOCC

### Serial Compilation

```bash
$ modmap -m aocc
$ module load aocc/<version>
```

**Compilers:**
- `clang`, `clang++`, `flang`

Example:
```bash
$ flang -o myexec myprog.f90
```

For full compiler options, refer to the [AOCC User Guide](https://docs.amd.com/r/en-US/57222-AOCC-user-guide/Command-line-Options).

### MPI Wrappers

```bash
$ module load openmpi/<version>
$ mpicc -o myexec myprog.c
```

---

## Basic MPI Execution

To test if your parallel executable works:

```bash
$ module load <mpi module>
$ mpirun ./myexec
```

**Interactive Job Example:**

```bash
$ salloc -N 2 --ntasks-per-node=1 --gres=gpu:1 --time=01:00:00
$ srun -n 2 ./myexec
```

**Batch Job Example:**

```bash
#!/bin/bash
#SBATCH --job-name=test
#SBATCH -N2 --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00

module load <mpi module>
mpirun ./myexec
```

---

## Totalview

Totalview must be executed on the compute nodes that run parallel code.

### Steps to use Totalview via RCM:

1. **Setup `.tvdrc` in `$HOME/.totalview`:**
```bash
dset -set_as_default TV::bulk_launch_enabled true
dset -set_as_default TV::bulk_launch_string {srun --mem-per-cpu=0 -N%N -n%N -w`awk -F. 'BEGIN {ORS=","} {if (NR==%N) ORS=""; print $1}' %t1` -l --input=none %B/tvdsvr%K -callback_host %H -callback_ports %L -set_pws %P -verbosity %V -working_directory %D %F}
```

2. **Submit Job Script**
```bash
#!/bin/bash
#SBATCH -t 30:00 -N 1 -A <account>
#SBATCH -p g100_usr_prod
module load totalview
tvconnect srun ./your_executable
$ sbatch job.sh
```

3. **Open Totalview GUI and connect.**

---

## Installing packages with Python environment

```bash
$ module load python/<version>
$ python -m venv my_env
$ source my_env/bin/activate
$ pip install <package>
```

**Notes:**
- Create environments in `$WORK` (not `$HOME`).
- Deactivate with `deactivate`.

For optimized Python/AI environments see:
- [Cineca-ai module](https://docs.hpc.cineca.it/hpc/hpc_cineca-ai-hpyc.html#cineca-ai-card)
- [Cineca-hpyc module](https://docs.hpc.cineca.it/hpc/hpc_cineca-ai-hpyc.html#cineca-hpyc-card)

---

## SPACK

Spack is a multi-platform package manager for HPC environments.

### Quick Usage

```bash
$ module load spack/<version>
$ spack spec -Il <package>
$ spack install <package>
$ module load <package>
```

### Installing a New Package

Default locations (Leonardo example):
```
$PUBLIC/spack-<version>/install
$PUBLIC/spack-<version>/modules
$PUBLIC/spack-<version>/user_cache
```

### Listing Software

```bash
$ spack list <package>
$ spack find
$ spack info <package>
```

### Add a Compiler

```bash
$ module load <compiler>
$ spack compiler add
```

### Variants and Dependencies

```bash
$ spack spec -Il <package> +cuda -debug ^openmpi
$ spack install <package> +cuda ^openmpi
```

### Module Command and Managing

```bash
$ spack module tcl refresh --upstream-modules <package>
$ module use $PUBLIC/spack-<version>/modules
$ module av <package_module>
```

---

© 2025 CINECA User Support Team  
Built with [Sphinx](https://www.sphinx-doc.org/) using the [Read the Docs theme](https://github.com/readthedocs/sphinx_rtd_theme).
