"""
System configuration management for HPC-ScaleTest.
Provides System and SystemPartition classes for HPC system configuration.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from .environments import Environment, ProgrammingEnvironment
from .types import SchedulerBackend, LauncherBackend, ModuleBackend

logger = logging.getLogger(__name__)


class ProcessorInfo:
    """Information about processor configuration."""
    
    def __init__(self, arch=None, model=None, platform=None, num_cpus=None,
                 num_cpus_per_core=None, num_cpus_per_socket=None, 
                 num_sockets=None, topology=None):
        self.arch = arch
        self.model = model
        self.platform = platform
        self.num_cpus = num_cpus
        self.num_cpus_per_core = num_cpus_per_core
        self.num_cpus_per_socket = num_cpus_per_socket
        self.num_sockets = num_sockets
        self.topology = topology
    
    @property
    def num_cores(self) -> Optional[int]:
        """Calculate total number of cores."""
        if self.num_cpus and self.num_cpus_per_core:
            return self.num_cpus // self.num_cpus_per_core
        return None
    
    @property
    def num_cores_per_socket(self) -> Optional[int]:
        """Calculate cores per socket."""
        if self.num_cores and self.num_sockets:
            return self.num_cores // self.num_sockets
        return None
    
    @property
    def num_numa_nodes(self) -> Optional[int]:
        """Get number of NUMA nodes."""
        if self.topology and 'numa_nodes' in self.topology:
            return len(self.topology['numa_nodes'])
        return None
    
    @property
    def num_cores_per_numa_node(self) -> Optional[int]:
        """Calculate cores per NUMA node."""
        if self.num_numa_nodes and self.num_cores:
            return self.num_cores // self.num_numa_nodes
        return None


class DeviceInfo:
    """Information about devices (GPUs, etc.)."""
    
    def __init__(self, type, arch=None, model=None, num_devices=1):
        self.type = type
        self.arch = arch
        self.model = model
        self.num_devices = num_devices
    
    @property
    def device_type(self) -> str:
        """Get device type."""
        return self.type


class SystemPartition:
    """Represents a system partition (queue/partition)."""
    
    def __init__(self, name, parent_system, scheduler, launcher, description="",
                 access=None, resources=None, environs=None, local_env=None,
                 max_jobs=1, prepare_cmds=None, processor=None, devices=None,
                 extras=None, features=None, time_limit=None):
        self.name = name
        self.parent_system = parent_system
        self.scheduler = scheduler
        self.launcher = launcher
        self.description = description
        self.access = access or []
        self.resources = resources or {}
        self.environs = environs or []
        self.local_env = local_env
        self.max_jobs = max_jobs
        self.prepare_cmds = prepare_cmds or []
        self.processor = processor
        self.devices = devices or []
        self.extras = extras or {}
        self.features = features or []
        self.time_limit = time_limit
        
        # Add implicit extras
        self.extras.setdefault('scheduler', self.scheduler.value)
        self.extras.setdefault('launcher', self.launcher.value)
    
    @property
    def fullname(self) -> str:
        """Get fully qualified name."""
        return f'{self.parent_system}:{self.name}'
    
    def get_resource(self, name: str, **values) -> List[str]:
        """Get resource configuration with values substituted."""
        ret = []
        for r in self.resources.get(name, []):
            try:
                ret.append(r.format(**values))
            except KeyError:
                pass
        return ret
    
    def get_environment(self, name: str) -> Optional[ProgrammingEnvironment]:
        """Get environment by name."""
        for env in self.environs:
            if env.name == name:
                return env
        return None
    
    def select_devices(self, devtype: str) -> List[DeviceInfo]:
        """Select devices by type."""
        return [d for d in self.devices if d.device_type == devtype]
    
    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, SystemPartition):
            return False
        
        return (self.name == other.name and
                self.scheduler == other.scheduler and
                self.launcher == other.launcher and
                self.access == other.access and
                self.environs == other.environs and
                self.resources == other.resources and
                self.local_env == other.local_env)
    
    def __hash__(self):
        return hash(self.fullname)


class System:
    """Represents an HPC system."""
    
    def __init__(self, name, description="", hostnames=None, modules_system=ModuleBackend.LMOD,
                 preload_env=None, prefix=None, outputdir=None, resourcesdir=None,
                 stagedir=None, partitions=None):
        self.name = name
        self.description = description
        self.hostnames = hostnames or []
        self.modules_system = modules_system
        self.preload_env = preload_env
        self.prefix = prefix
        self.outputdir = outputdir
        self.resourcesdir = resourcesdir
        self.stagedir = stagedir
        self.partitions = partitions or []
    
    def get_partition(self, name: str) -> Optional[SystemPartition]:
        """Get partition by name."""
        for partition in self.partitions:
            if partition.name == name:
                return partition
        return None
    
    def get_default_partition(self) -> Optional[SystemPartition]:
        """Get default partition (first one)."""
        return self.partitions[0] if self.partitions else None
    
    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, System):
            return False
        
        return (self.name == other.name and
                self.hostnames == other.hostnames and
                self.partitions == other.partitions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'hostnames': self.hostnames,
            'modules_system': self.modules_system.value,
            'modules': [m for m in self.preload_env.modules] if self.preload_env else [],
            'env_vars': list(self.preload_env.env_vars.items()) if self.preload_env else [],
            'prefix': str(self.prefix) if self.prefix else None,
            'outputdir': str(self.outputdir) if self.outputdir else None,
            'stagedir': str(self.stagedir) if self.stagedir else None,
            'resourcesdir': str(self.resourcesdir) if self.resourcesdir else None,
            'partitions': [self._partition_to_dict(p) for p in self.partitions]
        }
    
    def _partition_to_dict(self, partition: SystemPartition) -> Dict[str, Any]:
        """Convert partition to dictionary."""
        return {
            'name': partition.name,
            'description': partition.description,
            'scheduler': partition.scheduler.value,
            'launcher': partition.launcher.value,
            'access': partition.access,
            'resources': [
                {'name': name, 'options': options}
                for name, options in partition.resources.items()
            ],
            'environs': [e.name for e in partition.environs],
            'max_jobs': partition.max_jobs,
            'modules': [m for m in partition.local_env.modules] if partition.local_env else [],
            'env_vars': list(partition.local_env.env_vars.items()) if partition.local_env else [],
            'prepare_cmds': partition.prepare_cmds,
            'processor': partition.processor.__dict__ if partition.processor else None,
            'devices': [d.__dict__ for d in partition.devices],
            'extras': partition.extras,
            'features': partition.features,
            'time_limit': partition.time_limit
        }


class SystemManager:
    """Manager for system configurations."""
    
    def __init__(self):
        self.systems: Dict[str, System] = {}
        self.current_system: Optional[System] = None
    
    def add_system(self, system: System):
        """Add a system configuration."""
        self.systems[system.name] = system
        logger.info(f"Added system: {system.name}")
    
    def get_system(self, name: str) -> Optional[System]:
        """Get system by name."""
        return self.systems.get(name)
    
    def detect_system(self) -> Optional[System]:
        """Detect current system based on hostname."""
        import socket
        hostname = socket.gethostname()
        
        for system in self.systems.values():
            for pattern in system.hostnames:
                if self._match_hostname(hostname, pattern):
                    logger.info(f"Detected system: {system.name}")
                    return system
        
        logger.warning(f"No system configuration found for hostname: {hostname}")
        return None
    
    def _match_hostname(self, hostname: str, pattern: str) -> bool:
        """Match hostname against pattern."""
        import fnmatch
        return fnmatch.fnmatch(hostname, pattern)
    
    def set_current_system(self, system: System):
        """Set current system."""
        self.current_system = system
        logger.info(f"Set current system: {system.name}")
    
    def get_current_system(self) -> Optional[System]:
        """Get current system."""
        return self.current_system
    
    def validate_system(self, system: System) -> List[str]:
        """Validate system configuration."""
        errors = []
        
        if not system.name:
            errors.append("System name is required")
        
        if not system.partitions:
            errors.append("At least one partition is required")
        
        for partition in system.partitions:
            partition_errors = self._validate_partition(partition)
            errors.extend([f"{partition.name}: {error}" for error in partition_errors])
        
        return errors
    
    def _validate_partition(self, partition: SystemPartition) -> List[str]:
        """Validate partition configuration."""
        errors = []
        
        if not partition.name:
            errors.append("Partition name is required")
        
        if partition.max_jobs < 1:
            errors.append("max_jobs must be >= 1")
        
        if not partition.environs:
            errors.append("At least one environment is required")
        
        return errors
    
    def load_from_config(self, config: Dict[str, Any]) -> System:
        """Load system configuration from dictionary."""
        # This would be implemented to parse YAML/JSON config
        # For now, return a basic system
        system = System(
            name=config.get('name', 'unknown'),
            description=config.get('description', ''),
            hostnames=config.get('hostnames', []),
            modules_system=ModuleBackend(config.get('modules_system', 'lmod'))
        )
        
        # Load partitions
        for part_config in config.get('partitions', []):
            partition = self._load_partition_from_config(part_config, system.name)
            system.partitions.append(partition)
        
        return system
    
    def _load_partition_from_config(self, config: Dict[str, Any], system_name: str) -> SystemPartition:
        """Load partition from configuration."""
        return SystemPartition(
            name=config['name'],
            parent_system=system_name,
            scheduler=SchedulerBackend(config.get('scheduler', 'slurm')),
            launcher=LauncherBackend(config.get('launcher', 'srun')),
            description=config.get('description', ''),
            access=config.get('access', []),
            resources=config.get('resources', {}),
            max_jobs=config.get('max_jobs', 1),
            prepare_cmds=config.get('prepare_cmds', []),
            time_limit=config.get('time_limit')
        )


# Global system manager instance
system_manager = SystemManager()
