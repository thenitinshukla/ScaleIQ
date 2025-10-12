"""
Test runner with auto-build.
"""

import logging
import json
import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from core.test_definition import Test
from core.config import JobConfig
from core.factory import BackendFactory
from core.types import JobStatus, SchedulerBackend, LauncherBackend, ModuleBackend, BuildBackend
from core.abstracts import DefaultResultParser
from engine.scaling import ScalingEngine
from utils.file_utils import create_directory, write_file
from utils.decorators import run_before, check_binary_and_compile


logger = logging.getLogger(__name__)


class TestRunner:
    def __init__(self, test: Test):
        self.test = test
        test.validate()
        
        # Output dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scaling_type = test.scaling_config.scaling_type.value
        self.run_dir = test.output_dir / f"{test.name}_{scaling_type}_{timestamp}"
        create_directory(self.run_dir)
        logger.info(f"Output dir: {self.run_dir}")
        
        # Load modules for build (improved for login node)
        self._load_modules_for_build()
        
        # Backends
        self.scheduler = BackendFactory.create_scheduler(
            test.backend_config.scheduler, test.backend_config.scheduler_options
        )
        launcher_backend = LauncherBackend.MPIRUN if test.backend_config.scheduler == SchedulerBackend.LOCAL else test.backend_config.launcher
        self.launcher = BackendFactory.create_launcher(
            launcher_backend, test.backend_config.launcher_options
        )
        self.module_system = BackendFactory.create_module_system(
            test.backend_config.module_system, test.backend_config.module_options
        )
        
        # Build if source_dir set
        self.install_dir = self._build_if_needed()
        
        # Update command with installed exe if built
        if self.install_dir:
            exe_name = test.build_config.executable_name
            self.test.command[0] = str(self.install_dir / exe_name)
            logger.info(f"Updated exe to installed: {self.test.command[0]}")
        
        self.scaling_engine = ScalingEngine(test.scaling_config, test.resource_config)
    
    def _load_modules_for_build(self):
        """Load modules reliably on login node (bash -l for profile)."""
        modules = self.test.environment_config.modules
        if not modules:
            logger.info("No modules to load for build")
            return
        
        module_backend = self.test.backend_config.module_system
        module_system = BackendFactory.create_module_system(module_backend)
        load_cmds = module_system.generate_load_commands(modules)
        
        if load_cmds:
            full_cmd = " && ".join(load_cmds) + " && source /etc/profile"  # Source profile for env
            bash_cmd = f"bash -l -c '{full_cmd} && which mpicc'"  # Login shell, check MPI
            logger.info(f"Loading modules for build: {bash_cmd}")
            try:
                result = subprocess.run(bash_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                mpicc_path = result.stdout.decode().strip()
                if mpicc_path and os.path.exists(mpicc_path):
                    logger.info(f"MPI found: {mpicc_path}")
                    # Set env vars for CMake
                    os.environ['CC'] = 'mpicc'
                    os.environ['CXX'] = 'mpicxx'
                    os.environ['FC'] = 'mpifort'  # If Fortran
                    os.environ['PATH'] = f"{os.path.dirname(mpicc_path)}:{os.environ.get('PATH', '')}"
                else:
                    logger.warning("MPI not found after load—build may fail (use pre-built exe)")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Module load failed (non-fatal): {e.stderr.decode()}. Build may skip MPI.")
    
    def _build_if_needed(self) -> Optional[Path]:
        """Build if source_dir set."""
        source_dir = self.test.build_config.source_dir
        if not source_dir or not source_dir.exists():
            return None
        
        build_system = self.test.backend_config.build_system or BuildBackend.CMAKE
        builder = BackendFactory.create_build_system(build_system, self.test.backend_config.build_options)
        
        build_dir = self.test.build_config.build_dir or source_dir / "build"
        install_dir = self.test.build_config.install_dir or self.run_dir / "install"
        
        # Flags with MPI env (now set) + HDF5 (common for iPIC3D)
        effective_flags = {
            **self.test.build_config.build_flags,
            "CMAKE_BUILD_TYPE": "Release",
            "HDF5_ROOT": "/opt/intel/oneapi/hdf5/latest"  # Adjust if needed; or from env
        }
        
        logger.info(f"Building from {source_dir} using {build_system.value}")
        if not builder.configure(source_dir, build_dir, effective_flags):
            logger.warning("Build configure failed—skipping auto-build (use pre-built)")
            return None  # Non-fatal: Fall back to command[0] as-is
        if not builder.build(build_dir, self.test.build_config.parallel_jobs):
            logger.warning("Build failed—skipping install")
            return None
        if not builder.install(build_dir, install_dir):
            logger.warning("Install failed")
            return None
        
        logger.info(f"Built and installed to {install_dir}")
        return install_dir
    
    @run_before('compile')
    @run_before("_check_binary")
    def run(self) -> bool:
        logger.info(f"Starting {self.test.name} ({self.test.scaling_config.scaling_type.value})")
        
        job_configs = self.scaling_engine.generate_job_configs()
        logger.info(f"Generated {len(job_configs)} configs")
        
        job_ids = {}
        for job_config in job_configs:
            job_id = self._submit_job(job_config)
            if job_id:
                job_ids[job_config.job_id] = job_id
                logger.info(f"Submitted {job_config.job_id}: {job_id}")
            else:
                return False
        
        results = self._monitor_jobs(job_ids)
        self._generate_summary(job_configs, results)
        
        failures = [k for k, v in results.items() if v != JobStatus.COMPLETED]
        if failures:
            logger.warning(f"Failures: {failures}")
            return False
        logger.info("All complete")
        return True
    
    def compile(self):
        """Compile the code if needed."""
        logger.info("Checking if compilation is needed")
        self.install_dir = self._build_if_needed()
        
        # Update command with installed exe if built
        if self.install_dir:
            exe_name = self.test.build_config.executable_name
            installed_exe_path = self.install_dir / exe_name
            if installed_exe_path.exists():
                self.test.command[0] = str(installed_exe_path)
                logger.info(f"Updated exe to installed: {self.test.command[0]}")
    
    def _check_binary(self):
        """Check if the binary exists, and build if it doesn't."""
        # Get the executable path from the command
        exe_path = Path(self.test.command[0])
        
        # Check if the binary exists at the specified path
        if exe_path.exists():
            logger.info(f"Binary found at specified path: {exe_path}")
            return True
        
        # If it's a relative path, check common locations
        if not exe_path.is_absolute():
            # Check in current directory
            if (Path.cwd() / exe_path).exists():
                self.test.command[0] = str(Path.cwd() / exe_path)
                logger.info(f"Binary found in current directory: {self.test.command[0]}")
                return True
            
            # Check in source build directory
            source_dir = self.test.build_config.source_dir
            if source_dir and source_dir.exists():
                # Check in source_dir/build/
                build_exe_path = source_dir / "build" / exe_path
                if build_exe_path.exists():
                    self.test.command[0] = str(build_exe_path)
                    logger.info(f"Binary found in source build directory: {self.test.command[0]}")
                    return True
                
                # Check in source_dir directly
                source_exe_path = source_dir / exe_path
                if source_exe_path.exists():
                    self.test.command[0] = str(source_exe_path)
                    logger.info(f"Binary found in source directory: {self.test.command[0]}")
                    return True
        
        # If binary doesn't exist and we have source_dir, try to build it
        source_dir = self.test.build_config.source_dir
        if source_dir and source_dir.exists():
            logger.info(f"Binary not found at {exe_path}, attempting to build from {source_dir}")
            self.compile()
            
            # After compilation, check if the binary now exists in the install directory
            if self.install_dir:
                exe_name = self.test.build_config.executable_name
                installed_exe_path = self.install_dir / exe_name
                if installed_exe_path.exists():
                    self.test.command[0] = str(installed_exe_path)
                    logger.info(f"Binary found after compilation: {self.test.command[0]}")
                    return True
        
        logger.warning(f"Binary not found and build failed or not configured: {exe_path}")
        return False
    
    def _submit_job(self, job_config: JobConfig) -> Optional[str]:
        job_dir = self.run_dir / job_config.job_id
        create_directory(job_dir)
        job_config.working_dir = job_dir
        
        # Input file
        if self.test.input_file:
            input_path = job_dir / "Maxwell2D.inp"
            content = self.test.get_input_content(job_config)
            write_file(input_path, content)
            self.test.command[-1] = "Maxwell2D.inp"  # Ensure command uses it
        
        env_setup = self._generate_env_setup()
        launch_cmd = self.launcher.generate_launch_command(
            job_config, self.test.command, self.test.resource_config
        )
        
        script_content = self.scheduler.generate_job_script(
            job_config, self.test.resource_config, launch_cmd, env_setup
        )
        
        script_path = job_dir / "job.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        logger.info(f"Created job script: {script_path}")
        logger.debug(f"Job script content:\n{script_content}")
        
        try:
            logger.info(f"Submitting job script: {script_path}")
            job_id = self.scheduler.submit_job(script_path)
            logger.info(f"Successfully submitted job with ID: {job_id}")
            
            metadata = {
                'job_id': job_id,
                'num_nodes': job_config.num_nodes,
                'num_procs': job_config.num_procs,
                'procs_decomposition': job_config.procs_decomposition,
                'submitted_at': datetime.now().isoformat()
            }
            with open(job_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            return job_id
        except Exception as e:
            logger.error(f"Submit failed: {e}")
            return None
    
    def _generate_env_setup(self) -> List[str]:
        commands = []
        if self.test.environment_config.modules:
            commands.extend(self.module_system.generate_load_commands(self.test.environment_config.modules))
        for key, value in self.test.environment_config.env_vars.items():
            commands.append(f"export {key}={value}")
        commands.extend(self.test.environment_config.pre_commands)
        return commands
    
    def _monitor_jobs(self, job_ids: Dict[str, str]) -> Dict[str, JobStatus]:
        results = {}
        pending = set(job_ids.keys())
        while pending:
            for job_name in list(pending):
                job_id = job_ids[job_name]
                status = self.scheduler.get_job_status(job_id)
                if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT):
                    results[job_name] = status
                    pending.remove(job_name)
                    logger.info(f"{job_name}: {status.value}")
            if pending:
                time.sleep(10)
        return results
    
    def _generate_summary(self, job_configs: List[JobConfig], results: Dict[str, JobStatus]):
        summary = {
            'test_name': self.test.name,
            'scaling_type': self.test.scaling_config.scaling_type.value,
            'completed_at': datetime.now().isoformat(),
            'jobs': []
        }
        parser = DefaultResultParser()
        for config in job_configs:
            job_dir = self.run_dir / config.job_id
            job_info = {
                'job_id': config.job_id,
                'num_nodes': config.num_nodes,
                'num_procs': config.num_procs,
                'status': results.get(config.job_id, JobStatus.UNKNOWN).value
            }
            out_files = list(job_dir.glob("out_*.out"))
            if out_files:
                metrics = parser.parse_output(out_files[0])
                job_info['metrics'] = metrics
                if 'wall_time' in metrics:
                    job_info['wall_time'] = metrics['wall_time']
            summary['jobs'].append(job_info)
        
        summary_path = self.run_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary: {summary_path}")