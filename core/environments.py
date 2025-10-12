"""
Environment management system for HPC-ScaleTest.
Provides robust environment module integration with compiler flag resolution.
"""

import os
import subprocess
import logging
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def normalize_module_list(modules: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Normalize module list to consistent format.
    
    Args:
        modules: List of modules (strings or dicts)
        
    Returns:
        List of normalized module dictionaries
    """
    ret = []
    for m in modules:
        if isinstance(m, str):
            ret.append({'name': m, 'collection': False, 'path': None})
        else:
            ret.append(m)
    return ret


class Environment:
    """Environment configuration for running tests.
    
    Represents a collection of modules, environment variables, and commands
    to be loaded when this environment is activated.
    """
    
    def __init__(self, name, modules=None, env_vars=None, extras=None, 
                 features=None, prepare_cmds=None):
        self.name = name
        self.modules = modules or []
        self.env_vars = env_vars or {}
        self.extras = extras or {}
        self.features = features or []
        self.prepare_cmds = prepare_cmds or []
        
        # Normalize modules after initialization
        self._modules = normalize_module_list(self.modules)
        self._module_names = [m['name'] for m in self._modules]
        
        # Convert env_vars values to strings
        if isinstance(self.env_vars, dict):
            self._env_vars = {k: str(v) for k, v in self.env_vars.items()}
        else:
            self._env_vars = {}
    
    @property
    def module_names(self) -> List[str]:
        """Get list of module names."""
        return self._module_names
    
    @property
    def modules_detailed(self) -> List[Dict[str, Any]]:
        """Get detailed module information."""
        return self._modules
    
    def __eq__(self, other):
        """Check equality with another environment."""
        if not isinstance(other, Environment):
            return False
        
        return (self.name == other.name and
                set(self.module_names) == set(other.module_names) and
                self.env_vars == other.env_vars)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return (f'{type(self).__name__}('
                f'name={self.name!r}, '
                f'modules={self.modules!r}, '
                f'env_vars={list(self.env_vars.items())!r}, '
                f'extras={self.extras!r}, features={self.features!r})')


class ProgrammingEnvironment(Environment):
    """Programming environment with compiler and flag support.
    
    Extends Environment with compiler-specific properties and flags.
    """
    
    def __init__(self, name, modules=None, env_vars=None, extras=None,
                 features=None, prepare_cmds=None, cc='cc', cxx='CC',
                 ftn='ftn', nvcc='nvcc', cppflags=None, cflags=None,
                 cxxflags=None, fflags=None, ldflags=None, resources=None):
        super().__init__(name, modules, env_vars, extras, features, prepare_cmds)
        
        # Compiler executables
        self.cc = cc
        self.cxx = cxx
        self.ftn = ftn
        self.nvcc = nvcc
        
        # Compiler flags
        self.cppflags = cppflags or []
        self.cflags = cflags or []
        self.cxxflags = cxxflags or []
        self.fflags = fflags or []
        self.ldflags = ldflags or []
        
        # Additional resources
        self.resources = resources or {}
    
    def _resolve_flags(self, flag_type: str, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Resolve compiler flags from environment variables.
        
        Args:
            flag_type: Type of flags (cflags, cxxflags, etc.)
            environ: Environment variables dict
            
        Returns:
            List of resolved flags
        """
        if environ is None:
            environ = os.environ
        
        flags = []
        
        # Get base flags from instance
        if flag_type == 'cppflags':
            flags.extend(self.cppflags)
        elif flag_type == 'cflags':
            flags.extend(self.cflags)
        elif flag_type == 'cxxflags':
            flags.extend(self.cxxflags)
        elif flag_type == 'fflags':
            flags.extend(self.fflags)
        elif flag_type == 'ldflags':
            flags.extend(self.ldflags)
        
        # Resolve from environment variables
        env_var = flag_type.upper()
        if env_var in environ:
            env_flags = environ[env_var].split()
            flags.extend(env_flags)
        
        return flags
    
    def get_cc(self, environ: Optional[Dict[str, str]] = None) -> str:
        """Get C compiler with environment resolution."""
        if environ and 'CC' in environ:
            return environ['CC']
        return self.cc
    
    def get_cxx(self, environ: Optional[Dict[str, str]] = None) -> str:
        """Get C++ compiler with environment resolution."""
        if environ and 'CXX' in environ:
            return environ['CXX']
        return self.cxx
    
    def get_ftn(self, environ: Optional[Dict[str, str]] = None) -> str:
        """Get Fortran compiler with environment resolution."""
        if environ and 'FC' in environ:
            return environ['FC']
        return self.ftn
    
    def get_nvcc(self, environ: Optional[Dict[str, str]] = None) -> str:
        """Get NVIDIA CUDA compiler with environment resolution."""
        if environ and 'NVCC' in environ:
            return environ['NVCC']
        return self.nvcc
    
    def get_cppflags(self, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Get preprocessor flags."""
        return self._resolve_flags('cppflags', environ)
    
    def get_cflags(self, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Get C compiler flags."""
        return self._resolve_flags('cflags', environ)
    
    def get_cxxflags(self, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Get C++ compiler flags."""
        return self._resolve_flags('cxxflags', environ)
    
    def get_fflags(self, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Get Fortran compiler flags."""
        return self._resolve_flags('fflags', environ)
    
    def get_ldflags(self, environ: Optional[Dict[str, str]] = None) -> List[str]:
        """Get linker flags."""
        return self._resolve_flags('ldflags', environ)


class EnvironmentSnapshot:
    """Snapshot of current environment for restoration."""
    
    def __init__(self, name: str = 'env_snapshot'):
        self.name = name
        self._env_vars = dict(os.environ)
    
    def restore(self):
        """Restore environment from snapshot."""
        os.environ.clear()
        os.environ.update(self._env_vars)
    
    def __eq__(self, other):
        """Check equality with another snapshot."""
        if not isinstance(other, EnvironmentSnapshot):
            return False
        
        return (self.name == other.name and
                self._env_vars == other._env_vars)


def create_environment_snapshot() -> EnvironmentSnapshot:
    """Create a snapshot of the current environment."""
    return EnvironmentSnapshot()


class ModuleSystemManager:
    """Manager for environment module systems."""
    
    def __init__(self, module_system: str = 'lmod'):
        self.module_system = module_system
        self._validate_module_system()
    
    def _validate_module_system(self):
        """Validate that the module system is available."""
        try:
            if self.module_system == 'lmod':
                subprocess.run(['module', '--version'], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            elif self.module_system in ['tmod', 'tmod4']:
                subprocess.run(['module', '--version'], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            else:
                logger.warning(f"Unknown module system: {self.module_system}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"Module system {self.module_system} not available")
    
    def load_modules(self, modules: List[str]) -> List[str]:
        """Generate commands to load modules.
        
        Args:
            modules: List of module names to load
            
        Returns:
            List of shell commands to load modules
        """
        if not modules:
            return []
        
        commands = []
        for module in modules:
            if self.module_system == 'lmod':
                commands.append(f'module load {module}')
            elif self.module_system in ['tmod', 'tmod4']:
                commands.append(f'module load {module}')
            else:
                logger.warning(f"Unknown module system: {self.module_system}")
                break
        
        return commands
    
    def unload_modules(self, modules: List[str]) -> List[str]:
        """Generate commands to unload modules."""
        if not modules:
            return []
        
        commands = []
        for module in modules:
            if self.module_system == 'lmod':
                commands.append(f'module unload {module}')
            elif self.module_system in ['tmod', 'tmod4']:
                commands.append(f'module unload {module}')
        
        return commands
    
    def purge_modules(self) -> List[str]:
        """Generate commands to purge all modules."""
        if self.module_system == 'lmod':
            return ['module purge']
        elif self.module_system in ['tmod', 'tmod4']:
            return ['module purge']
        return []
    
    def list_loaded_modules(self):
        """List currently loaded modules."""
        try:
            if self.module_system == 'lmod':
                result = subprocess.run(['module', 'list'], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return self._parse_module_list(result.stdout.decode())
            elif self.module_system in ['tmod', 'tmod4']:
                result = subprocess.run(['module', 'list'], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return self._parse_module_list(result.stdout.decode())
        except subprocess.CalledProcessError:
            logger.warning("Failed to list loaded modules")
        
        return []
    
    def _parse_module_list(self, output: str) -> List[str]:
        """Parse module list output."""
        modules = []
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('Currently') and not line.startswith('---'):
                # Extract module name (before any version info)
                module_name = line.split()[0] if line.split() else ''
                if module_name:
                    modules.append(module_name)
        return modules
    
    def is_module_available(self, module):
        """Check if a module is available."""
        try:
            if self.module_system == 'lmod':
                result = subprocess.run(['module', 'avail', module], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return module in result.stdout.decode()
            elif self.module_system in ['tmod', 'tmod4']:
                result = subprocess.run(['module', 'avail', module], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return module in result.stdout.decode()
        except subprocess.CalledProcessError:
            pass
        
        return False


class EnvironmentManager:
    """High-level environment management."""
    
    def __init__(self, module_system: str = 'lmod'):
        self.module_manager = ModuleSystemManager(module_system)
        self.current_env: Optional[Environment] = None
        self.snapshot: Optional[EnvironmentSnapshot] = None
    
    def activate_environment(self, env: Environment) -> bool:
        """Activate an environment.
        
        Args:
            env: Environment to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create snapshot of current state
            self.snapshot = create_environment_snapshot()
            
            # Load modules
            if env.module_names:
                load_commands = self.module_manager.load_modules(env.module_names)
                for cmd in load_commands:
                    # Execute module load command
                    result = subprocess.run(['bash', '-c', cmd], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        logger.warning(f"Failed to load module: {cmd}")
            
            # Set environment variables
            for key, value in env.env_vars.items():
                os.environ[key] = value
            
            # Execute prepare commands
            for cmd in env.prepare_cmds:
                result = subprocess.run(['bash', '-c', cmd], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    logger.warning(f"Prepare command failed: {cmd}")
            
            self.current_env = env
            logger.info(f"Activated environment: {env.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate environment {env.name}: {e}")
            return False
    
    def deactivate_environment(self) -> bool:
        """Deactivate current environment."""
        try:
            if self.current_env:
                # Unload modules
                if self.current_env.module_names:
                    unload_commands = self.module_manager.unload_modules(
                        self.current_env.module_names)
                    for cmd in unload_commands:
                        subprocess.run(['bash', '-c', cmd], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Restore snapshot
                if self.snapshot:
                    self.snapshot.restore()
                
                logger.info(f"Deactivated environment: {self.current_env.name}")
                self.current_env = None
                self.snapshot = None
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to deactivate environment: {e}")
            return False
    
    def get_current_environment(self) -> Optional[Environment]:
        """Get currently active environment."""
        return self.current_env
    
    def validate_environment(self, env: Environment) -> List[str]:
        """Validate an environment configuration.
        
        Args:
            env: Environment to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check module availability
        for module in env.module_names:
            if not self.module_manager.is_module_available(module):
                errors.append(f"Module not available: {module}")
        
        # Check environment variables
        for key, value in env.env_vars.items():
            if not key or not value:
                errors.append(f"Invalid environment variable: {key}={value}")
        
        return errors
