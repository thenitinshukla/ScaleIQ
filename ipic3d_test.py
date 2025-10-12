#!/usr/bin/env python3
"""
Complete working example for HPC-ScaleTest adapted for iPIC3D.

This example demonstrates weak scaling for iPIC3D on a Slurm cluster.

To run this example:
1. Local testing (strong scaling only, limited):
   python scaletest.py run --test example_test.py --backend local --max-nodes 1 --scaling strong

2. On Slurm cluster (weak scaling):
   python scaletest.py run --test example_test.py --max-nodes 4

3. Validation:
   python scaletest.py validate --test example_test.py
"""

from pathlib import Path
from core.test_definition import Test
from core.types import ScalingType
from types import MethodType


def create_ipic3d_strong_scaling_test():
    """
    Create a comprehensive iPIC3D strong scaling test.

    Fixed problem size, scaling from 1 to 4 nodes.

    Returns:
        Test: Configured test instance
    """

    # Base input file path
    base_input = Path("/leonardo_scratch/large/userinternal/nshukla1/SpaceBenchmark/weak_scaling/test2/base/scaling")

    # Create test instance
    test = Test(
        name="ipic3d_strong_scaling",
        input_file=base_input,
        command=["/leonardo_scratch/large/userinternal/nshukla1/PICKTH/iPIC3D-CPU-SPACE-CoE/build/iPIC3D"]
    )

    # Configure environment modules
    test.set_modules([
        "intel-oneapi-compilers/2023.2.1",
        "intel-oneapi-mpi/2021.10.0",
        "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
    ])

    # Set environment variables
    test.set_env({
        "OMP_NUM_THREADS": "1",
    })

    # Configure backend components
    test.set_backend(
        scheduler="slurm",
        launcher="srun",
        module_system="lmod",
    )

    # Configure computational resources
    test.set_resources(
        max_nodes=4,
        procs_per_node=112,
        gpus_per_node=0,
        time_limit="02:00:00",
        partition="dcgp_usr_prod",
        account="cin_staff",
        mail_user="n.shukla@cineca.it"
    )

    # Configure scaling parameters (strong: fixed size)
    test.set_scaling(
        scaling_type="strong",
        max_nodes=4,
        initial_procs=(14, 8, 1),  # Initial decomposition: 112 procs
        initial_domain=(40.96, 20.48, 1.0),
        initial_cells=(896, 512, 1)
    )

    return test


def create_ipic3d_weak_scaling_test():
    """
    Create an iPIC3D weak scaling test.

    Problem size grows proportionally with processors.

    Returns:
        Test: Configured test instance
    """

    # Base input file path
    base_input = Path("/leonardo_scratch/large/userinternal/nshukla1/SpaceBenchmark/weak_scaling/test2/base/scaling")

    # Create test instance
    test = Test(
        name="ipic3d_weak_scaling",
        input_file=base_input,
        command=["/leonardo_scratch/large/userinternal/nshukla1/PICKTH/iPIC3D-CPU-SPACE-CoE/build/iPIC3D"]
    )

    # Configure environment modules
    test.set_modules([
        "intel-oneapi-compilers/2023.2.1",
        "intel-oneapi-mpi/2021.10.0",
        "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
    ])

    # Set environment variables
    test.set_env({
        "OMP_NUM_THREADS": "1",
    })

    # Configure backend components
    test.set_backend(
        scheduler="slurm",
        launcher="srun",
        module_system="lmod",
    )

    # Configure computational resources
    test.set_resources(
        max_nodes=4,
        procs_per_node=112,
        gpus_per_node=0,
        time_limit="02:00:00",
        partition="dcgp_usr_prod",
        account="cin_staff",
        mail_user="n.shukla@cineca.it"
    )

    # Configure scaling parameters (weak: growing size)
    test.set_scaling(
        scaling_type="weak",
        max_nodes=4,
        initial_procs=(14, 8, 1),  # Initial: 112 procs
        initial_domain=(40.96, 20.48, 1.0),
        initial_cells=(896, 512, 1)
    )

    # Override input generation for weak scaling (scale parameters in input file)
    def weak_get_input_content(self, job_config):
        base_content = self.input_file.read_text()
        lines = base_content.splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Lx"):
                new_lines.append(f"Lx = {job_config.domain_size[0]:.2f}")
            elif stripped.startswith("Ly"):
                new_lines.append(f"Ly = {job_config.domain_size[1]:.2f}")
            elif stripped.startswith("Lz"):
                new_lines.append(f"Lz = {job_config.domain_size[2]:.2f}")
            elif stripped.startswith("nxc"):
                new_lines.append(f"nxc = {int(job_config.cell_count[0])}")
            elif stripped.startswith("nyc"):
                new_lines.append(f"nyc = {int(job_config.cell_count[1])}")
            elif stripped.startswith("nzc"):
                new_lines.append(f"nzc = {int(job_config.cell_count[2])}")
            elif stripped.startswith("XLEN"):
                new_lines.append(f"XLEN = {job_config.procs_decomposition[0]}")
            elif stripped.startswith("YLEN"):
                new_lines.append(f"YLEN = {job_config.procs_decomposition[1]}")
            elif stripped.startswith("ZLEN"):
                new_lines.append(f"ZLEN = {job_config.procs_decomposition[2]}")
            else:
                new_lines.append(line)
        return "\n".join(new_lines) + "\n"

    test.get_input_content = MethodType(weak_get_input_content, test)

    return test


# Export the default test (weak scaling for iPIC3D)
test = create_ipic3d_weak_scaling_test()


# Alternative: Export multiple tests
tests = {
    'strong': create_ipic3d_strong_scaling_test(),
    'weak': create_ipic3d_weak_scaling_test(),
}


if __name__ == '__main__':
    """
    When run directly, print test configuration.
    """
    print("=" * 70)
    print("HPC-ScaleTest: iPIC3D Example")
    print("=" * 70)
    print()

    # Show weak scaling configuration
    weak_test = create_ipic3d_weak_scaling_test()

    print("Weak Scaling Test Configuration:")
    print(f"  Name: {weak_test.name}")
    print(f"  Input: {weak_test.input_file} (dynamically scaled)")
    print(f"  Command: {' '.join(weak_test.command)}")
    print(f"  Scaling: {weak_test.scaling_config.scaling_type.value}")
    print(f"  Max nodes: {weak_test.scaling_config.max_nodes}")
    print(f"  Initial procs: {weak_test.scaling_config.initial_procs[0]} x "
          f"{weak_test.scaling_config.initial_procs[1]} x {weak_test.scaling_config.initial_procs[2]}")
    print(f"  Initial problem size: {weak_test.scaling_config.initial_cells[0]} x "
          f"{weak_test.scaling_config.initial_cells[1]} x {weak_test.scaling_config.initial_cells[2]} cells")
    print()

    print("To run this test:")
    print("  Cluster (weak): python scaletest.py run --test example_test.py --max-nodes 4")
    print("  Cluster (strong): python scaletest.py run --test example_test.py --scaling strong --max-nodes 4")
    print("  Local (strong only): python scaletest.py run --test example_test.py --backend local --scaling strong --max-nodes 1")
    print()
    print("To validate:")
    print("  python scaletest.py validate --test example_test.py")
    print()
