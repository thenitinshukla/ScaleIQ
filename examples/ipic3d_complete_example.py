#!/usr/bin/env python3
"""
Complete iPIC3D scaling test example with robust environment management.
Demonstrates all features of the enhanced HPC-ScaleTest framework.

This example shows:
- Environment module integration with compiler flag resolution
- Robust build system with dependency handling
- Comprehensive validation and error handling
- Advanced result parsing and metrics extraction
- System configuration management.

To run this example:
1. Validate configuration:
   python scaletest.py validate --test examples/ipic3d_complete_example.py

2. Run weak scaling test:
   python scaletest.py run --test examples/ipic3d_complete_example.py --max-nodes 4

3. Run strong scaling test:
   python scaletest.py run --test examples/ipic3d_complete_example.py --scaling strong --max-nodes 4

4. Run with custom output directory:
   python scaletest.py run --test examples/ipic3d_complete_example.py --output ./my_results
"""

import sys
from pathlib import Path

# Add the project root to the Python path to enable proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.test_definition import Test
from core.types import ScalingType, SchedulerBackend, LauncherBackend, ModuleBackend
from core.environments import ProgrammingEnvironment
from core.systems import System, SystemPartition, ProcessorInfo, DeviceInfo
from core.validation import validate_test_configuration
from utils.decorators import run_before, check_binary_and_compile
from types import MethodType


def create_ipic3d_programming_environment():
    """Create a comprehensive programming environment for iPIC3D."""
    
    # Create programming environment with compiler flags
    env = ProgrammingEnvironment(
        name="ipic3d_intel_mpi",
        modules=[
            "intel-oneapi-compilers/2023.2.1",
            "intel-oneapi-mpi/2021.10.0", 
            "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
        ],
        env_vars={
            "OMP_NUM_THREADS": "1",
            "OMP_PROC_BIND": "close",
            "OMP_PLACES": "cores",
            "I_MPI_PIN_PROCESSOR_LIST": "all:map=scatter",
            "I_MPI_PIN_DOMAIN": "auto"
        },
        cc="mpicc",
        cxx="mpicxx", 
        ftn="mpifort",
        cflags=["-O3", "-xHost", "-qopenmp"],
        cxxflags=["-O3", "-xHost", "-qopenmp"],
        fflags=["-O3", "-xHost", "-qopenmp"],
        cppflags=["-DMPI", "-DHDF5"],
        ldflags=["-qopenmp", "-lhdf5"]
    )
    
    return env


def create_leonardo_system_config():
    """Create Leonardo system configuration."""
    
    # Processor information
    processor = ProcessorInfo(
        arch="x86_64",
        model="Intel Xeon Platinum 8358",
        platform="Intel",
        num_cpus=112,
        num_cpus_per_core=1,
        num_cpus_per_socket=56,
        num_sockets=2,
        topology={
            "numa_nodes": [
                {"cores": list(range(0, 56))},
                {"cores": list(range(56, 112))}
            ]
        }
    )
    
    # Create partition
    partition = SystemPartition(
        name="dcgp_usr_prod",
        parent_system="leonardo",
        scheduler=SchedulerBackend.SLURM,
        launcher=LauncherBackend.SRUN,
        description="Leonardo GPU partition",
        access=["--partition=dcgp_usr_prod"],
        resources={
            "gpu": ["--gres=gpu:1"],
            "memory": ["--mem=100GB"],
            "exclusive": ["--exclusive"]
        },
        environs=[create_ipic3d_programming_environment()],
        max_jobs=10,
        prepare_cmds=[
            "ulimit -s unlimited",
            "export OMP_NUM_THREADS=1"
        ],
        processor=processor,
        devices=[DeviceInfo(type="gpu", arch="sm_80", model="A100")],
        time_limit="02:00:00"
    )
    
    # Create system
    system = System(
        name="leonardo",
        description="Leonardo HPC System",
        hostnames=["leonardo*", "login*"],
        modules_system=ModuleBackend.LMOD,
        partitions=[partition]
    )
    
    return system


def create_ipic3d_weak_scaling_test():
    """Create iPIC3D weak scaling test with comprehensive configuration."""
    
    # Base paths
    base_input = Path("/leonardo_scratch/large/userinternal/nshukla1/SpaceBenchmark/weak_scaling/test2/base/scaling")
    source_dir = Path("/leonardo_scratch/large/userinternal/nshukla1/PICKTH/iPIC3D-CPU-SPACE-CoE")
    
    # Create test instance
    test = Test(
        name="ipic3d_weak_scaling_robust",
        command=["iPIC3D", "Maxwell2D.inp"],
        input_file=base_input,
        source_dir=source_dir,
        output_dir=Path("./results")
    )
    
    # Configure backend with enhanced options
    test.set_backend(
        scheduler="slurm",
        launcher="srun",
        module_system="lmod"
    )
    
    # Configure resources
    test.set_resources(
        max_nodes=4,
        procs_per_node=112,
        gpus_per_node=0,
        time_limit="02:00:00",
        partition="dcgp_usr_prod",
        account="cin_staff",
        mail_user="n.shukla@cineca.it",
        exclusive=True
    )
    
    # Configure scaling parameters
    test.set_scaling(
        scaling_type="weak",
        max_nodes=4,
        initial_procs=(14, 8, 1),  # 112 procs initial
        initial_domain=(40.96, 20.48, 1.0),
        initial_cells=(896, 512, 1)
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
        "OMP_PROC_BIND": "close",
        "OMP_PLACES": "cores",
        "I_MPI_PIN_PROCESSOR_LIST": "all:map=scatter",
        "I_MPI_PIN_DOMAIN": "auto"
    })
    
    # Custom input generation for weak scaling
    def weak_get_input_content(self, job_config):
        """Generate input content for weak scaling."""
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


def create_ipic3d_strong_scaling_test():
    """Create iPIC3D strong scaling test."""
    
    # Base paths
    base_input = Path("/leonardo_scratch/large/userinternal/nshukla1/SpaceBenchmark/weak_scaling/test2/base/scaling")
    source_dir = Path("/leonardo_scratch/large/userinternal/nshukla1/PICKTH/iPIC3D-CPU-SPACE-CoE")
    
    # Create test instance
    test = Test(
        name="ipic3d_strong_scaling_robust",
        command=["iPIC3D", "Maxwell2D.inp"],
        input_file=base_input,
        source_dir=source_dir,
        output_dir=Path("./results")
    )
    
    # Configure backend
    test.set_backend(
        scheduler="slurm",
        launcher="srun",
        module_system="lmod"
    )
    
    # Configure resources
    test.set_resources(
        max_nodes=4,
        procs_per_node=112,
        gpus_per_node=0,
        time_limit="02:00:00",
        partition="dcgp_usr_prod",
        account="cin_staff",
        mail_user="n.shukla@cineca.it"
    )
    
    # Configure scaling parameters (strong: fixed problem size)
    test.set_scaling(
        scaling_type="strong",
        max_nodes=4,
        initial_procs=(14, 8, 1),  # 112 procs initial
        initial_domain=(40.96, 20.48, 1.0),
        initial_cells=(896, 512, 1)
    )
    
    # Configure environment
    test.set_modules([
        "intel-oneapi-compilers/2023.2.1",
        "intel-oneapi-mpi/2021.10.0",
        "hdf5/1.14.3--intel-oneapi-mpi--2021.10.0--oneapi--2023.2.0"
    ])
    
    test.set_env({
        "OMP_NUM_THREADS": "1",
        "OMP_PROC_BIND": "close",
        "OMP_PLACES": "cores"
    })
    
    return test


def validate_and_display_config(test):
    """Validate configuration and display results."""
    print("=" * 80)
    print("HPC-ScaleTest: iPIC3D Complete Example")
    print("=" * 80)
    print()
    
    # Validate configuration
    validation_result = validate_test_configuration(test)
    
    if validation_result.is_valid:
        print("✓ Configuration validation passed")
    else:
        print("✗ Configuration validation failed:")
        for error in validation_result.errors:
            print(f"  ERROR: {error}")
    
    if validation_result.warnings:
        print("⚠ Configuration warnings:")
        for warning in validation_result.warnings:
            print(f"  WARNING: {warning}")
    
    print()
    print("Test Configuration:")
    print(f"  Name: {test.name}")
    print(f"  Command: {' '.join(test.command)}")
    print(f"  Input file: {test.input_file}")
    print(f"  Source directory: {test.build_config.source_dir}")
    print(f"  Output directory: {test.output_dir}")
    print(f"  Scaling type: {test.scaling_config.scaling_type.value}")
    print(f"  Max nodes: {test.scaling_config.max_nodes}")
    print(f"  Initial processors: {test.scaling_config.initial_procs}")
    print(f"  Initial domain: {test.scaling_config.initial_domain}")
    print(f"  Initial cells: {test.scaling_config.initial_cells}")
    print()
    print("Backend Configuration:")
    print(f"  Scheduler: {test.backend_config.scheduler.value}")
    print(f"  Launcher: {test.backend_config.launcher.value}")
    print(f"  Module system: {test.backend_config.module_system.value}")
    print()
    print("Resource Configuration:")
    print(f"  Max nodes: {test.resource_config.max_nodes}")
    print(f"  Procs per node: {test.resource_config.procs_per_node}")
    print(f"  Time limit: {test.resource_config.time_limit}")
    print(f"  Partition: {test.resource_config.partition}")
    print(f"  Account: {test.resource_config.account}")
    print()
    print("Environment Configuration:")
    print(f"  Modules: {test.environment_config.modules}")
    print(f"  Environment variables: {test.environment_config.env_vars}")
    print()
    
    return validation_result.is_valid


# Export the default test (weak scaling)
test = create_ipic3d_weak_scaling_test()

# Export multiple tests
tests = {
    'weak': create_ipic3d_weak_scaling_test(),
    'strong': create_ipic3d_strong_scaling_test(),
}

# Export system configuration
system_config = create_leonardo_system_config()


if __name__ == '__main__':
    """When run directly, validate and display configuration."""
    
    # Validate weak scaling test
    weak_test = create_ipic3d_weak_scaling_test()
    is_valid = validate_and_display_config(weak_test)
    
    if is_valid:
        print("Usage Examples:")
        print()
        print("1. Validate configuration:")
        print("   python scaletest.py validate --test examples/ipic3d_complete_example.py")
        print()
        print("2. Run weak scaling test:")
        print("   python scaletest.py run --test examples/ipic3d_complete_example.py --max-nodes 4")
        print()
        print("3. Run strong scaling test:")
        print("   python scaletest.py run --test examples/ipic3d_complete_example.py --scaling strong --max-nodes 4")
        print()
        print("4. Run with custom output directory:")
        print("   python scaletest.py run --test examples/ipic3d_complete_example.py --output ./my_results")
        print()
        print("5. Run with verbose logging:")
        print("   python scaletest.py run --test examples/ipic3d_complete_example.py --verbose")
        print()
        
        # Display system configuration
        print("System Configuration:")
        print(f"  System: {system_config.name}")
        print(f"  Description: {system_config.description}")
        print(f"  Hostnames: {system_config.hostnames}")
        print(f"  Module system: {system_config.modules_system.value}")
        print(f"  Partitions: {[p.name for p in system_config.partitions]}")
        print()
        
        # Display partition details
        for partition in system_config.partitions:
            print(f"Partition: {partition.name}")
            print(f"  Scheduler: {partition.scheduler.value}")
            print(f"  Launcher: {partition.launcher.value}")
            print(f"  Max jobs: {partition.max_jobs}")
            print(f"  Time limit: {partition.time_limit}")
            print(f"  Environments: {[e.name for e in partition.environs]}")
            if partition.processor:
                print(f"  Processor: {partition.processor.model} ({partition.processor.num_cpus} cores)")
            print()
    else:
        print("Configuration validation failed. Please fix the errors above.")
        exit(1)