"""
Unit tests for backend implementations.
"""

import unittest
from pathlib import Path
from core.factory import BackendFactory
from core.types import (
    SchedulerBackend, LauncherBackend,
    ModuleBackend, BuildBackend
)
from core.config import JobConfig, ResourceConfig


class TestSchedulerBackends(unittest.TestCase):
    """Test scheduler backends."""
    
    def test_local_scheduler_creation(self):
        """Test local scheduler instantiation."""
        scheduler = BackendFactory.create_scheduler(SchedulerBackend.LOCAL)
        self.assertIsNotNone(scheduler)
    
    def test_slurm_scheduler_creation(self):
        """Test Slurm scheduler instantiation."""
        scheduler = BackendFactory.create_scheduler(SchedulerBackend.SLURM)
        self.assertIsNotNone(scheduler)
    
    def test_job_script_generation(self):
        """Test job script generation."""
        scheduler = BackendFactory.create_scheduler(SchedulerBackend.LOCAL)
        
        job_config = JobConfig(
            job_id="test_job",
            num_nodes=1,
            num_procs=4,
            procs_decomposition=(2, 2, 1)
        )
        
        resource_config = ResourceConfig(
            max_nodes=1,
            procs_per_node=4
        )
        
        script = scheduler.generate_job_script(
            job_config,
            resource_config,
            ["echo", "test"],
            ["export TEST=1"]
        )
        
        self.assertIn("#!/bin/bash", script)
        self.assertIn("echo test", script)


class TestLauncherBackends(unittest.TestCase):
    """Test launcher backends."""
    
    def test_srun_launcher_creation(self):
        """Test srun launcher instantiation."""
        launcher = BackendFactory.create_launcher(LauncherBackend.SRUN)
        self.assertIsNotNone(launcher)
    
    def test_mpirun_launcher_creation(self):
        """Test mpirun launcher instantiation."""
        launcher = BackendFactory.create_launcher(LauncherBackend.MPIRUN)
        self.assertIsNotNone(launcher)
    
    def test_launch_command_generation(self):
        """Test launch command generation."""
        launcher = BackendFactory.create_launcher(LauncherBackend.SRUN)
        
        job_config = JobConfig(
            job_id="test_job",
            num_nodes=2,
            num_procs=256,
            procs_decomposition=(4, 4, 4)
        )
        
        resource_config = ResourceConfig(
            max_nodes=2,
            procs_per_node=128
        )
        
        cmd = launcher.generate_launch_command(
            job_config,
            ["./myapp"],
            resource_config
        )
        
        self.assertIn("srun", cmd)
        self.assertIn("-N", cmd)
        self.assertIn("./myapp", cmd)
    
    def test_gpu_binding_support(self):
        """Test GPU binding capability."""
        srun = BackendFactory.create_launcher(LauncherBackend.SRUN)
        mpirun = BackendFactory.create_launcher(LauncherBackend.MPIRUN)
        
        self.assertTrue(srun.supports_gpu_binding())
        self.assertFalse(mpirun.supports_gpu_binding())


class TestModuleBackends(unittest.TestCase):
    """Test module system backends."""
    
    def test_nomod_backend_creation(self):
        """Test no-module backend instantiation."""
        modules = BackendFactory.create_module_system(ModuleBackend.NOMOD)
        self.assertIsNotNone(modules)
    
    def test_lmod_backend_creation(self):
        """Test Lmod backend instantiation."""
        modules = BackendFactory.create_module_system(ModuleBackend.LMOD)
        self.assertIsNotNone(modules)
    
    def test_load_commands_generation(self):
        """Test module load command generation."""
        modules = BackendFactory.create_module_system(ModuleBackend.LMOD)
        
        commands = modules.generate_load_commands(["gcc/11.2.0", "openmpi/4.1.1"])
        
        self.assertEqual(len(commands), 2)
        self.assertIn("module load gcc/11.2.0", commands[0])
        self.assertIn("module load openmpi/4.1.1", commands[1])
    
    def test_nomod_returns_empty(self):
        """Test that nomod backend returns empty commands."""
        modules = BackendFactory.create_module_system(ModuleBackend.NOMOD)
        
        commands = modules.generate_load_commands(["gcc", "openmpi"])
        
        self.assertEqual(len(commands), 0)


class TestBuildBackends(unittest.TestCase):
    """Test build system backends."""
    
    def test_make_backend_creation(self):
        """Test make backend instantiation."""
        builder = BackendFactory.create_build_system(BuildBackend.MAKE)
        self.assertIsNotNone(builder)
    
    def test_cmake_backend_creation(self):
        """Test CMake backend instantiation."""
        builder = BackendFactory.create_build_system(BuildBackend.CMAKE)
        self.assertIsNotNone(builder)
    
    def test_autotools_backend_creation(self):
        """Test autotools backend instantiation."""
        builder = BackendFactory.create_build_system(BuildBackend.AUTOTOOLS)
        self.assertIsNotNone(builder)


if __name__ == '__main__':
    unittest.main()
