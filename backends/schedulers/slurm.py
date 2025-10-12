"""
Slurm scheduler backend with full sbatch integration.
Customized for user template: gres, exclusive, qos, mpirun/srun, timing, modules, etc.
"""

import subprocess
import logging
import re
import time
from pathlib import Path
from typing import List, Optional

from core.abstracts import SchedulerInterface
from core.config import JobConfig, ResourceConfig
from core.types import JobStatus, LARGE_JOB_THRESHOLD


logger = logging.getLogger(__name__)


class SlurmScheduler(SchedulerInterface):
    """Slurm workload manager backend."""
    
    def generate_job_script(
        self,
        job_config: JobConfig,
        resource_config: ResourceConfig,
        command: List[str],
        env_setup: List[str]
    ) -> str:
        """Generate Slurm batch script matching user template."""
        script = """#!/bin/bash

echo "======================================"
echo "======================================"
echo "This is my script"
cat $0
echo "======================================"
echo "======================================"

"""
        
        # Slurm directives
        script += f"#SBATCH --nodes={job_config.num_nodes}\n"
        script += f"#SBATCH --partition={resource_config.partition or 'X_usr_prod'}\n"
        if resource_config.qos:
            script += f"###SBATCH --qos={resource_config.qos}\n"
        script += f"#SBATCH --ntasks-per-node={resource_config.procs_per_node}\n"
        script += "#SBATCH --cpus-per-task=1\n"
        if resource_config.gpus_per_node > 0:
            script += f"#SBATCH --gres=gpu:{resource_config.gpus_per_node}\n"
        if resource_config.exclusive:
            script += "###SBATCH --exclusive\n"
        script += f"#SBATCH -A {resource_config.account or 'cin_X'}\n"
        script += f"#SBATCH --time={resource_config.time_limit}\n"
        script += f"#SBATCH --job-name={job_config.job_id}\n"
        script += f"#SBATCH -o {job_config.working_dir}/out_%j\n"
        script += f"#SBATCH -e {job_config.working_dir}/err_%j\n"
        
        if resource_config.mail_user:
            script += f"#SBATCH --mail-type=ALL\n"
            script += f"#SBATCH --mail-user={resource_config.mail_user}\n"
        
        if resource_config.constraint:
            script += f"#SBATCH --constraint={resource_config.constraint}\n"
        
        if resource_config.reservation:
            script += f"#SBATCH --reservation={resource_config.reservation}\n"
        
        if resource_config.memory_per_node:
            script += f"#SBATCH --mem={resource_config.memory_per_node}\n"
        
        # Large job handling
        if job_config.num_nodes > LARGE_JOB_THRESHOLD:
            script += "# Large job: adjust qos if needed\n"
        
        script += "\n# Environment setup\n"
        for cmd in env_setup:
            script += f"{cmd}\n"
        
        script += '\necho "Loading modules"\n'
        
        script += "\n# Change to working directory\n"
        if job_config.working_dir:
            script += f"cd {job_config.working_dir}\n"
        
        script += "export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}\n"
        
        script += "date\n"
        
        # Main command with timing (use provided launch command)
        script += 'start_time="$(date -u +%s.%N)"\n'
        script += "# Execute command\n"
        script += " ".join(command) + "\n\n"
        script += 'end_time="$(date -u +%s.%N)"\n'
        script += 'elapsed="$(bc <<<"$end_time-$start_time")"\n'
        script += 'echo "Total of $elapsed seconds elapsed for process"\n'
        
        script += "date\n"
        
        return script
    
    def submit_job(self, script_path: Path) -> str:
        """Submit job using sbatch."""
        try:
            result = subprocess.run(
                ["sbatch", str(script_path)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse job ID
            match = re.search(r'Submitted batch job (\d+)', result.stdout)
            if match:
                job_id = match.group(1)
                logger.debug(f"Submitted Slurm job {job_id}")
                return job_id
            else:
                raise ValueError(f"Could not parse job ID from: {result.stdout}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"sbatch failed: {e.stderr}")
            raise
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """Query job status using squeue/sacct."""
        try:
            # squeue first
            result = subprocess.run(
                ["squeue", "-j", job_id, "-h", "-o", "%T"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                state = result.stdout.strip().upper()
                return self._parse_slurm_state(state)
            
            # sacct for completed
            result = subprocess.run(
                ["sacct", "-j", job_id, "-n", "-o", "State"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                state = result.stdout.strip().split()[0].upper()
                return self._parse_slurm_state(state)
            
            return JobStatus.UNKNOWN
            
        except Exception as e:
            logger.error(f"Failed to query job status: {e}")
            return JobStatus.UNKNOWN
    
    def _parse_slurm_state(self, state: str) -> JobStatus:
        """Convert Slurm state to JobStatus."""
        state_map = {
            'PENDING': JobStatus.PENDING,
            'RUNNING': JobStatus.RUNNING,
            'COMPLETED': JobStatus.COMPLETED,
            'FAILED': JobStatus.FAILED,
            'CANCELLED': JobStatus.CANCELLED,
            'TIMEOUT': JobStatus.TIMEOUT,
            'NODE_FAIL': JobStatus.FAILED,
            'PREEMPTED': JobStatus.CANCELLED,
        }
        return state_map.get(state, JobStatus.UNKNOWN)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel job using scancel."""
        try:
            subprocess.run(
                ["scancel", job_id],
                check=True,
                capture_output=True
            )
            logger.info(f"Cancelled job {job_id}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"scancel failed: {e.stderr}")
            return False
    
    def wait_for_completion(
        self,
        job_id: str,
        timeout: Optional[int] = None
    ) -> JobStatus:
        """Wait for job to complete."""
        start_time = time.time()
        while True:
            status = self.get_job_status(job_id)
            if status not in (JobStatus.PENDING, JobStatus.RUNNING):
                return status
            if timeout and (time.time() - start_time) > timeout:
                return JobStatus.TIMEOUT
            time.sleep(10)
