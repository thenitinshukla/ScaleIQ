# ====================
# core/__init__.py
# ====================
"""
Core abstractions and types for HPC-ScaleTest.
"""

from .types import (
    ScalingType,
    SchedulerBackend,
    LauncherBackend,
    ModuleBackend,
    BuildBackend,
    JobStatus
)
from .test_definition import Test
from .factory import BackendFactory
from .environments import (
    Environment,
    ProgrammingEnvironment,
    EnvironmentManager,
    ModuleSystemManager
)
from .systems import (
    System,
    SystemPartition,
    ProcessorInfo,
    DeviceInfo,
    SystemManager
)
from .validation import (
    ConfigurationValidator,
    EnvironmentValidator,
    SystemValidator,
    ValidationResult,
    validate_test_configuration,
    validate_environment,
    validate_programming_environment,
    validate_system
)

__all__ = [
    # Types and enums
    'ScalingType',
    'SchedulerBackend',
    'LauncherBackend',
    'ModuleBackend',
    'BuildBackend',
    'JobStatus',
    
    # Test definition
    'Test',
    
    # Factory
    'BackendFactory',
    
    # Environment management
    'Environment',
    'ProgrammingEnvironment',
    'EnvironmentManager',
    'ModuleSystemManager',
    
    # System management
    'System',
    'SystemPartition',
    'ProcessorInfo',
    'DeviceInfo',
    'SystemManager',
    
    # Validation
    'ConfigurationValidator',
    'EnvironmentValidator',
    'SystemValidator',
    'ValidationResult',
    'validate_test_configuration',
    'validate_environment',
    'validate_programming_environment',
    'validate_system'
]

