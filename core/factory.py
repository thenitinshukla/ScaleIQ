"""
Factory for creating backend instances.
"""

from typing import Dict, Optional

from .abstracts import (
    SchedulerInterface, LauncherInterface,
    ModuleSystemInterface, BuildSystemInterface
)
from .types import (
    SchedulerBackend, LauncherBackend,
    ModuleBackend, BuildBackend
)


class BackendFactory:
    """Factory for creating backend plugin instances."""
    
    @staticmethod
    def create_scheduler(
        backend: SchedulerBackend,
        options: Optional[Dict] = None
    ) -> SchedulerInterface:
        """Create a scheduler backend instance."""
        if backend == SchedulerBackend.LOCAL:
            from backends.schedulers.local import LocalScheduler
            return LocalScheduler(options)
        elif backend == SchedulerBackend.SLURM:
            from backends.schedulers.slurm import SlurmScheduler
            return SlurmScheduler(options)
        elif backend == SchedulerBackend.PBS:
            raise NotImplementedError("PBS backend not yet implemented")
        else:
            raise ValueError(f"Unknown scheduler backend: {backend}")
    
    @staticmethod
    def create_launcher(
        backend: LauncherBackend,
        options: Optional[Dict] = None
    ) -> LauncherInterface:
        """Create a launcher backend instance."""
        if backend == LauncherBackend.SRUN:
            from backends.launchers.srun import SrunLauncher
            return SrunLauncher(options)
        elif backend in (LauncherBackend.MPIRUN, LauncherBackend.MPIEXEC):
            from backends.launchers.mpirun import MpiRunLauncher
            return MpiRunLauncher(options)
        else:
            raise ValueError(f"Unknown launcher backend: {backend}")
    
    @staticmethod
    def create_module_system(
        backend: ModuleBackend,
        options: Optional[Dict] = None
    ) -> ModuleSystemInterface:
        """Create a module system backend instance."""
        if backend == ModuleBackend.NOMOD:
            from backends.modules.nomod import NoModBackend
            return NoModBackend(options)
        elif backend == ModuleBackend.TMOD:
            from backends.modules.tmod import TModBackend
            return TModBackend(options)
        elif backend == ModuleBackend.TMOD4:
            from backends.modules.tmod4 import TMod4Backend
            return TMod4Backend(options)
        elif backend == ModuleBackend.LMOD:
            from backends.modules.lmod import LModBackend
            return LModBackend(options)
        else:
            raise ValueError(f"Unknown module backend: {backend}")
    
    @staticmethod
    def create_build_system(
        backend: BuildBackend,
        options: Optional[Dict] = None
    ) -> BuildSystemInterface:
        """Create a build system backend instance."""
        if backend == BuildBackend.MAKE:
            from backends.builds.make import MakeBackend
            return MakeBackend(options)
        elif backend == BuildBackend.CMAKE:
            from backends.builds.cmake import CMakeBackend
            return CMakeBackend(options)
        elif backend == BuildBackend.AUTOTOOLS:
            from backends.builds.autotools import AutotoolsBackend
            return AutotoolsBackend(options)
        elif backend == BuildBackend.EASYBUILD:
            from backends.builds.easybuild import EasyBuildBackend
            return EasyBuildBackend(options)
        elif backend == BuildBackend.SPACK:
            from backends.builds.spack import SpackBackend
            return SpackBackend(options)
        else:
            raise ValueError(f"Unknown build backend: {backend}")
