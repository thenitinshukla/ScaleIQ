#!/usr/bin/env python3
"""
Simple iPIC3D example: Build from source, run weak scaling.
Update paths below to your setup.
"""

from pathlib import Path
from core.test_definition import Test


def create_ipic3d_test():
    """Simple: Build from source, run weak scaling."""
    source_dir = Path("/leonardo_scratch/large/userinternal/nshukla1/hpc-scaletest2/iPIC3D-CPU-SPACE-CoE")  # Your source
    test = Test(
        name="ipic3d_weak",
        command=["./iPIC3D", "Maxwell2D.inp"],  # Exe + input name
        input_file=Path("/leonardo_scratch/large/userinternal/nshukla1/hpc-scaletest2/iPIC3D-CPU-SPACE-CoE/inputfiles/Maxwell2D.inp"),  # Your base input
        source_dir=source_dir,  # Auto-build
        output_dir=Path("./results")
    )
    
    # Modules (adjust for your system)
    test.set_modules([
        "intel-oneapi-compilers/2023.2.1",
        "intel-oneapi-mpi/2021.10.0",
        "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
    ])
    
    # Env
    test.set_env({
        "OMP_NUM_THREADS": "1",
    })
    
    # Backend
    test.set_backend(scheduler="slurm", launcher="mpirun", module_system="lmod")
    
    # Resources (adjust partition/account)
    test.set_resources(
        max_nodes=2,
        procs_per_node=112,  # Your procs/node
        gpus_per_node=0,
        time_limit="02:00:00",
        partition="dcgp_usr_prod",
        account="cin_staff",
        mail_user="n.shukla@cineca.it"
    )
    
    # Scaling: Weak, initial from your input (adjust if needed)
    test.set_scaling(
        scaling_type="weak",
        max_nodes=2,
        initial_procs=(14, 8, 1),  # XLEN=14, YLEN=8, ZLEN=1 (112 procs)
        initial_domain=(40.96, 20.48, 1.0),  # Lx,Ly,Lz from your input
        initial_cells=(896, 512, 1)  # nxc,nyc,nzc
    )
    
    # Build config
    test.build_config.executable_name = "iPIC3D"  # Main exe
    test.build_config.build_flags = {"CMAKE_BUILD_TYPE": "Release"}
    
    return test


# Module-level export: Required for loading
test = create_ipic3d_test()


if __name__ == '__main__':
    """
    Print config when run directly.
    """
    print("=" * 70)
    print("iPIC3D Weak Scaling Test")
    print("=" * 70)
    print()
    print(f"Name: {test.name}")
    print(f"Build from: {test.build_config.source_dir}")
    print(f"Input: {test.input_file}")
    print(f"Command: {' '.join(test.command)}")
    print(f"Scaling: {test.scaling_config.scaling_type.value} up to {test.scaling_config.max_nodes} nodes")
    print(f"Initial procs: {test.scaling_config.initial_procs[0]}x{test.scaling_config.initial_procs[1]}x{test.scaling_config.initial_procs[2]}")
    print(f"Initial cells: {test.scaling_config.initial_cells[0]}x{test.scaling_config.initial_cells[1]}x{test.scaling_config.initial_cells[2]}")
    print()
    print("Run: python scaletest.py run --test examples/example_test.py")
    print()
