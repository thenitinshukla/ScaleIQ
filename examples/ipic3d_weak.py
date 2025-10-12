#!/usr/bin/env python3
"""
iPIC3D Weak Scaling Test for HPC-ScaleTest.

Runs weak scaling on iPIC3D-CPU-SPACE-CoE repo.
- Builds with CMake.
- Loads Leonardo modules.
- Scales domain/cells/topology automatically.
- Assumes input file 'ipic3D_weakscaling_test' in working dir.

Run:
  python scaletest.py run --test ipic3d_weak.py --scaling weak --max-nodes 8
  (For local debug: --backend local --max-nodes 1)
"""

from pathlib import Path
from core.test_definition import Test


def create_ipic3d_weak_test():
    repo_path = Path("/leonardo_scratch/large/userinternal/nshukla1/PICKTH/iPIC3D-CPU-SPACE-CoE")
    input_path = Path("ipic3D_weakscaling_test")  # Your provided input file

    test = Test(
        name="ipic3d_weakscaling",
        command=["./iPIC3D", "ipic3D_weakscaling_test"],  # Executable + input
        input_file=input_path,
    )

    # Environment: Load Leonardo modules
    test.set_modules([
        "intel-oneapi-compilers/2023.2.1",
        "intel-oneapi-mpi/2021.10.0",
        "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
    ])

    # Backend: Slurm + srun + Lmod + CMake
    test.set_backend(
        scheduler="slurm",
        launcher="srun",
        module_system="lmod",
        build_system="cmake"
    )

    # Resources: Leonardo CPU partition, full node
    test.set_resources(
        max_nodes=8,  # Scale up to 8 nodes (adjust as needed)
        procs_per_node=112,  # Cores/node
        gpus_per_node=0,
        memory_per_node="200GB",  # Adjust based on needs
        time_limit="01:00:00",
        partition="dcec",  # Data Centric General Purpose
        account="userinternal",  # Adjust to your project/account
    )

    # Weak scaling: Scale domain/cells with procs
    test.set_scaling(
        scaling_type="weak",
        max_nodes=8,  # Up to 8 nodes (896 total procs)
        initial_procs=(14, 8, 1),  # Initial topology (112 procs = 1 node)
        initial_domain=(40.96, 20.48, 1.0),  # Initial Lx, Ly, Lz
        initial_cells=(896, 512, 1),  # Initial nxc, nyc, nzc
        # node_sequence=[1, 2, 4, 8]  # Optional: custom (default powers of 2)
    )

    # Build: CMake from repo
    test.set_build(
        source_dir=repo_path,
        build_dir=None,  # Auto: output/build
        install_dir=None,  # Auto: output/install (executable here)
        build_flags={"CMAKE_BUILD_TYPE": "Release"},  # Optional flags
        parallel_jobs=8
    )

    # Pre/post commands (optional)
    test.add_pre_command("echo 'Starting iPIC3D weak scaling job'")
    test.add_post_command("echo 'iPIC3D job completed'")

    return test


# Export default test
test = create_ipic3d_weak_test()


if __name__ == "__main__":
    test = create_ipic3d_weak_test()
    print("iPIC3D Weak Scaling Configuration:")
    print(f"  Name: {test.name}")
    print(f"  Repo: {test.build_config.source_dir}")
    print(f"  Input: {test.input_file}")
    print(f"  Command: {' '.join(test.command)}")
    print(f"  Modules: {', '.join(test.environment_config.modules)}")
    print(f"  Scaling: {test.scaling_config.scaling_type.value} (up to {test.scaling_config.max_nodes} nodes)")
    print(f"  Initial procs: {test.scaling_config.initial_procs}")
    print(f"  Initial cells: {test.scaling_config.initial_cells}")
    print(f"  Procs/node: {test.resource_config.procs_per_node}")
    print()
    print("Run with: python scaletest.py run --test ipic3d_weak.py --scaling weak --max-nodes 8")
    print("Validate: python scaletest.py validate --test ipic3d_weak.py")
