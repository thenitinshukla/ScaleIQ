"""
Configuration classes for test definition.
"""

from pathlib import Path
from typing import Optional, Dict, List

from .types import (
    ScalingType, SchedulerBackend, LauncherBackend, 
    ModuleBackend, BuildBackend,
    ProcsDecomposition, DomainSize, CellCount,
    DEFAULT_PROCS_PER_NODE, DEFAULT_TIME_LIMIT
)


class BackendConfig:
    """Configuration for backend systems."""
    
    def __init__(self, scheduler=SchedulerBackend.LOCAL, launcher=LauncherBackend.SRUN, 
                 module_system=ModuleBackend.NOMOD, build_system=None,
                 scheduler_options=None, launcher_options=None, 
                 module_options=None, build_options=None):
        self.scheduler = scheduler
        self.launcher = launcher
        self.module_system = module_system
        self.build_system = build_system
        self.scheduler_options = scheduler_options or {}
        self.launcher_options = launcher_options or {}
        self.module_options = module_options or {}
        self.build_options = build_options or {}


class ResourceConfig:
    """Configuration for computational resources."""
    
    def __init__(self, max_nodes=1, procs_per_node=DEFAULT_PROCS_PER_NODE, 
                 gpus_per_node=0, memory_per_node=None, time_limit=DEFAULT_TIME_LIMIT,
                 exclusive=False, qos=None, partition=None, account=None,
                 constraint=None, reservation=None, mail_user=None):
        self.max_nodes = max_nodes
        self.procs_per_node = procs_per_node
        self.gpus_per_node = gpus_per_node
        self.memory_per_node = memory_per_node
        self.time_limit = time_limit
        self.exclusive = exclusive
        self.qos = qos
        self.partition = partition
        self.account = account
        self.constraint = constraint
        self.reservation = reservation
        self.mail_user = mail_user


class ScalingConfig:
    """Configuration for scaling tests."""
    
    def __init__(self, scaling_type=ScalingType.STRONG, max_nodes=1,
                 initial_procs=(1, 1, 1), initial_domain=None, 
                 initial_cells=None, node_sequence=None):
        self.scaling_type = scaling_type
        self.max_nodes = max_nodes
        self.initial_procs = initial_procs
        self.initial_domain = initial_domain
        self.initial_cells = initial_cells
        self.node_sequence = node_sequence
    
    def get_node_sequence(self):
        """Get the sequence of node counts for scaling."""
        if self.node_sequence:
            return self.node_sequence
        
        # Generate powers of 2 up to max_nodes
        sequence = []
        n = 1
        while n <= self.max_nodes:
            sequence.append(n)
            n *= 2
        
        # Ensure max_nodes is included if not a power of 2
        if sequence[-1] != self.max_nodes:
            sequence.append(self.max_nodes)
        
        return sequence


class EnvironmentConfig:
    """Configuration for environment setup."""
    
    def __init__(self, modules=None, env_vars=None, pre_commands=None, post_commands=None):
        self.modules = modules or []
        self.env_vars = env_vars or {}
        self.pre_commands = pre_commands or []
        self.post_commands = post_commands or []


class BuildConfig:
    """Configuration for building the application."""
    
    def __init__(self, source_dir=None, build_dir=None, install_dir=None,
                 build_flags=None, parallel_jobs=4, executable_name="main_exe"):
        self.source_dir = source_dir
        self.build_dir = build_dir
        self.install_dir = install_dir
        self.build_flags = build_flags or {}
        self.parallel_jobs = parallel_jobs
        self.executable_name = executable_name


class JobConfig:
    """Configuration for a single job instance."""
    
    def __init__(self, job_id, num_nodes, num_procs, procs_decomposition,
                 domain_size=None, cell_count=None, working_dir=None, output_file=None):
        self.job_id = job_id
        self.num_nodes = num_nodes
        self.num_procs = num_procs
        self.procs_decomposition = procs_decomposition
        self.domain_size = domain_size
        self.cell_count = cell_count
        self.working_dir = working_dir
        self.output_file = output_file
    
    def total_procs(self):
        """Calculate total number of processes."""
        px, py, pz = self.procs_decomposition
        return px * py * pz
