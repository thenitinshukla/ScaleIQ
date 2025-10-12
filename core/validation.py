"""
Comprehensive validation system for HPC-ScaleTest.
Provides validation for configurations, environments, and system compatibility.
"""

import logging
import subprocess
import socket
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from .config import BackendConfig, ResourceConfig, ScalingConfig, EnvironmentConfig, BuildConfig
from .test_definition import Test
from .types import SchedulerBackend, LauncherBackend, ModuleBackend, BuildBackend
from .environments import Environment, ProgrammingEnvironment
from .systems import System, SystemPartition

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation check."""
    
    def __init__(self, is_valid=True, errors=None, warnings=None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self):
        return self.is_valid
    
    def add_error(self, error):
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning):
        """Add a warning message."""
        self.warnings.append(warning)


class ConfigurationValidator:
    """Validator for test configurations."""
    
    def __init__(self):
        self.system_info = self._detect_system_info()
    
    def _detect_system_info(self) -> Dict[str, Any]:
        """Detect basic system information."""
        info = {
            'hostname': socket.gethostname(),
            'cpu_count': self._get_cpu_count(),
            'memory_gb': self._get_memory_gb(),
            'scheduler_available': self._check_scheduler_availability(),
            'module_system': self._detect_module_system()
        }
        return info
    
    def _get_cpu_count(self) -> int:
        """Get CPU count."""
        try:
            import os
            return os.cpu_count() or 1
        except:
            return 1
    
    def _get_memory_gb(self) -> float:
        """Get memory in GB."""
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        return kb / (1024 * 1024)
        except:
            pass
        return 0.0
    
    def _check_scheduler_availability(self) -> Dict[str, bool]:
        """Check which schedulers are available."""
        schedulers = {}
        for scheduler in SchedulerBackend:
            schedulers[scheduler.value] = self._check_command_available(scheduler.value)
        return schedulers
    
    def _detect_module_system(self) -> Optional[str]:
        """Detect available module system."""
        for module_sys in ['lmod', 'module']:
            if self._check_command_available(module_sys):
                return module_sys
        return None
    
    def _check_command_available(self, command):
        """Check if a command is available."""
        try:
            # Use 'where' on Windows and 'which' on Unix-like systems
            import platform
            if platform.system() == "Windows":
                subprocess.run(['where', command], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            else:
                subprocess.run(['which', command], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def validate_test(self, test: Test) -> ValidationResult:
        """Validate a complete test configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate basic test properties
        self._validate_test_basic(test, result)
        
        # Validate backend configuration
        self._validate_backend_config(test.backend_config, result)
        
        # Validate resource configuration
        self._validate_resource_config(test.resource_config, result)
        
        # Validate scaling configuration
        self._validate_scaling_config(test.scaling_config, result)
        
        # Validate environment configuration
        self._validate_environment_config(test.environment_config, result)
        
        # Validate build configuration
        self._validate_build_config(test.build_config, result)
        
        # Validate system compatibility
        self._validate_system_compatibility(test, result)
        
        return result
    
    def _validate_test_basic(self, test: Test, result: ValidationResult):
        """Validate basic test properties."""
        if not test.name:
            result.add_error("Test name is required")
        elif not test.name.replace('_', '').replace('-', '').isalnum():
            result.add_warning("Test name contains special characters")
        
        if not test.command:
            result.add_error("Test command is required")
        elif not isinstance(test.command, list):
            result.add_error("Test command must be a list")
        elif len(test.command) == 0:
            result.add_error("Test command cannot be empty")
        
        if test.input_file and not test.input_file.exists():
            result.add_error(f"Input file not found: {test.input_file}")
        
        if test.output_dir and not test.output_dir.parent.exists():
            result.add_error(f"Output directory parent does not exist: {test.output_dir.parent}")
    
    def _validate_backend_config(self, config: BackendConfig, result: ValidationResult):
        """Validate backend configuration."""
        # Check scheduler availability
        if not self.system_info['scheduler_available'].get(config.scheduler.value, False):
            if config.scheduler != SchedulerBackend.LOCAL:
                result.add_warning(f"Scheduler {config.scheduler.value} not available on this system")
        
        # Check module system availability
        if config.module_system != ModuleBackend.NOMOD:
            if not self.system_info['module_system']:
                result.add_warning(f"Module system {config.module_system.value} not available")
            elif config.module_system.value != self.system_info['module_system']:
                result.add_warning(f"Module system mismatch: configured {config.module_system.value}, "
                                 f"detected {self.system_info['module_system']}")
    
    def _validate_resource_config(self, config: ResourceConfig, result: ValidationResult):
        """Validate resource configuration."""
        if config.max_nodes < 1:
            result.add_error("max_nodes must be >= 1")
        
        if config.procs_per_node < 1:
            result.add_error("procs_per_node must be >= 1")
        
        if config.gpus_per_node < 0:
            result.add_error("gpus_per_node must be >= 0")
        
        # Check against system limits
        if config.procs_per_node > self.system_info['cpu_count']:
            result.add_warning(f"procs_per_node ({config.procs_per_node}) exceeds "
                             f"system CPU count ({self.system_info['cpu_count']})")
        
        # Validate time limit format
        if not self._is_valid_time_format(config.time_limit):
            result.add_error(f"Invalid time limit format: {config.time_limit}")
    
    def _validate_scaling_config(self, config: ScalingConfig, result: ValidationResult):
        """Validate scaling configuration."""
        if config.max_nodes < 1:
            result.add_error("scaling.max_nodes must be >= 1")
        
        # Validate initial decomposition
        if config.initial_procs:
            px, py, pz = config.initial_procs
            if px < 1 or py < 1 or pz < 1:
                result.add_error("Initial processor decomposition must have positive values")
        
        # Validate domain size
        if config.initial_domain:
            dx, dy, dz = config.initial_domain
            if dx <= 0 or dy <= 0 or dz <= 0:
                result.add_error("Initial domain size must have positive values")
        
        # Validate cell count
        if config.initial_cells:
            nx, ny, nz = config.initial_cells
            if nx < 1 or ny < 1 or nz < 1:
                result.add_error("Initial cell count must have positive values")
    
    def _validate_environment_config(self, config: EnvironmentConfig, result: ValidationResult):
        """Validate environment configuration."""
        # Check module availability
        if config.modules and self.system_info['module_system']:
            for module in config.modules:
                if not self._check_module_available(module):
                    result.add_warning(f"Module not available: {module}")
        
        # Validate environment variables
        for key, value in config.env_vars.items():
            if not key or not isinstance(key, str):
                result.add_error(f"Invalid environment variable name: {key}")
            if not isinstance(value, str):
                result.add_error(f"Environment variable value must be string: {key}")
    
    def _validate_build_config(self, config: BuildConfig, result: ValidationResult):
        """Validate build configuration."""
        if config.source_dir and not config.source_dir.exists():
            result.add_error(f"Source directory not found: {config.source_dir}")
        
        if config.build_dir and not config.build_dir.parent.exists():
            result.add_error(f"Build directory parent does not exist: {config.build_dir.parent}")
        
        if config.install_dir and not config.install_dir.parent.exists():
            result.add_error(f"Install directory parent does not exist: {config.install_dir.parent}")
        
        if config.parallel_jobs < 1:
            result.add_error("parallel_jobs must be >= 1")
        
        if config.parallel_jobs > self.system_info['cpu_count']:
            result.add_warning(f"parallel_jobs ({config.parallel_jobs}) exceeds "
                             f"system CPU count ({self.system_info['cpu_count']})")
    
    def _validate_system_compatibility(self, test: Test, result: ValidationResult):
        """Validate system compatibility."""
        # Check if running on login node vs compute node
        hostname = self.system_info['hostname']
        if any(keyword in hostname.lower() for keyword in ['login', 'head', 'master']):
            if test.backend_config.scheduler == SchedulerBackend.LOCAL:
                result.add_warning("Running local scheduler on login node - consider using batch scheduler")
        
        # Check memory requirements
        if test.resource_config.memory_per_node:
            try:
                required_gb = self._parse_memory_string(test.resource_config.memory_per_node)
                if required_gb > self.system_info['memory_gb']:
                    result.add_warning(f"Required memory ({required_gb:.1f}GB) exceeds "
                                     f"system memory ({self.system_info['memory_gb']:.1f}GB)")
            except ValueError:
                result.add_error(f"Invalid memory specification: {test.resource_config.memory_per_node}")
    
    def _check_module_available(self, module):
        """Check if a module is available."""
        try:
            if self.system_info['module_system'] == 'lmod':
                result = subprocess.run(['module', 'is-avail', module], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return result.returncode == 0
            else:
                result = subprocess.run(['module', 'avail', module], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return module in result.stdout.decode()
        except:
            return False
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """Check if time string is in valid format (HH:MM:SS)."""
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return False
            hours, minutes, seconds = map(int, parts)
            return 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60
        except:
            return False
    
    def _parse_memory_string(self, memory_str: str) -> float:
        """Parse memory string to GB."""
        memory_str = memory_str.upper().strip()
        if memory_str.endswith('GB'):
            return float(memory_str[:-2])
        elif memory_str.endswith('G'):
            return float(memory_str[:-1])
        elif memory_str.endswith('MB'):
            return float(memory_str[:-2]) / 1024
        elif memory_str.endswith('M'):
            return float(memory_str[:-1]) / 1024
        elif memory_str.endswith('TB'):
            return float(memory_str[:-2]) * 1024
        elif memory_str.endswith('T'):
            return float(memory_str[:-1]) * 1024
        else:
            # Assume GB if no unit
            return float(memory_str)


class EnvironmentValidator:
    """Validator for environment configurations."""
    
    def validate_environment(self, env: Environment) -> ValidationResult:
        """Validate an environment configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not env.name:
            result.add_error("Environment name is required")
        
        # Validate modules
        for module in env.module_names:
            if not module or not isinstance(module, str):
                result.add_error(f"Invalid module name: {module}")
        
        # Validate environment variables
        for key, value in env.env_vars.items():
            if not key or not isinstance(key, str):
                result.add_error(f"Invalid environment variable name: {key}")
            if not isinstance(value, str):
                result.add_error(f"Environment variable value must be string: {key}")
        
        # Validate prepare commands
        for cmd in env.prepare_cmds:
            if not cmd or not isinstance(cmd, str):
                result.add_error(f"Invalid prepare command: {cmd}")
        
        return result
    
    def validate_programming_environment(self, env: ProgrammingEnvironment) -> ValidationResult:
        """Validate a programming environment."""
        result = self.validate_environment(env)
        
        # Validate compiler executables
        compilers = [('cc', env.cc), ('cxx', env.cxx), ('ftn', env.ftn), ('nvcc', env.nvcc)]
        for name, compiler in compilers:
            if not compiler or not isinstance(compiler, str):
                result.add_error(f"Invalid {name} compiler: {compiler}")
        
        # Validate compiler flags
        flag_types = [
            ('cppflags', env.cppflags),
            ('cflags', env.cflags),
            ('cxxflags', env.cxxflags),
            ('fflags', env.fflags),
            ('ldflags', env.ldflags)
        ]
        
        for name, flags in flag_types:
            if not isinstance(flags, list):
                result.add_error(f"{name} must be a list")
            else:
                for flag in flags:
                    if not isinstance(flag, str):
                        result.add_error(f"Invalid {name} flag: {flag}")
        
        return result


class SystemValidator:
    """Validator for system configurations."""
    
    def validate_system(self, system: System) -> ValidationResult:
        """Validate a system configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not system.name:
            result.add_error("System name is required")
        
        if not system.partitions:
            result.add_error("At least one partition is required")
        
        # Validate partitions
        for partition in system.partitions:
            partition_result = self.validate_partition(partition)
            if not partition_result:
                result.errors.extend([f"{partition.name}: {error}" for error in partition_result.errors])
                result.warnings.extend([f"{partition.name}: {warning}" for warning in partition_result.warnings])
                result.is_valid = False
        
        return result
    
    def validate_partition(self, partition: SystemPartition) -> ValidationResult:
        """Validate a partition configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not partition.name:
            result.add_error("Partition name is required")
        
        if partition.max_jobs < 1:
            result.add_error("max_jobs must be >= 1")
        
        if not partition.environs:
            result.add_error("At least one environment is required")
        
        # Validate environments
        env_validator = EnvironmentValidator()
        for env in partition.environs:
            env_result = env_validator.validate_programming_environment(env)
            if not env_result:
                result.errors.extend([f"env {env.name}: {error}" for error in env_result.errors])
                result.warnings.extend([f"env {env.name}: {warning}" for warning in env_result.warnings])
                result.is_valid = False
        
        return result


# Global validator instances
config_validator = ConfigurationValidator()
env_validator = EnvironmentValidator()
system_validator = SystemValidator()


def validate_test_configuration(test: Test) -> ValidationResult:
    """Validate a test configuration."""
    return config_validator.validate_test(test)


def validate_environment(env: Environment) -> ValidationResult:
    """Validate an environment configuration."""
    return env_validator.validate_environment(env)


def validate_programming_environment(env: ProgrammingEnvironment) -> ValidationResult:
    """Validate a programming environment."""
    return env_validator.validate_programming_environment(env)


def validate_system(system: System) -> ValidationResult:
    """Validate a system configuration."""
    return system_validator.validate_system(system)
