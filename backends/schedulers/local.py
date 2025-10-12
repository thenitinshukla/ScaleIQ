"""
Local scheduler backend for running jobs as local processes.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional
import time
import signal

from core.abstracts import SchedulerInterface
from core.config import JobConfig, ResourceConfig
from core.types import JobStatus


logger = logging.getLogger(__name__)


class LocalScheduler(SchedulerInterface):
    """Run jobs as local processes."""
    
    def __init__(self, options: Optional[dict] = None):
        super().__init__(options)
        self.processes = {}  # job_id -> subprocess.Popen
    
    def generate_job_script(
        self,
        job_config: JobConfig,
        resource_config: ResourceConfig,
        command: List[str],
        env_setup: List[str]
    ) -> str:
        """Generate a bash script for local execution."""
        script = """#!/bin/bash

echo "======================================"
echo "======================================"
echo "This is my script"
cat $0
echo "======================================"
echo "======================================"

"""
        # Environment setup
        for cmd in env_setup:
            script += f"{cmd}\n"
        
        script += '\necho "Loading modules"\n'
        
        script += "\n# Change to working directory\n"
        if job_config.working_dir:
            script += f"cd {job_config.working_dir}\n\n"
        
        script += "export OMP_NUM_THREADS=1\n"  # Default for local
        
        script += "date\n"
        
        # Main command with timing
        script += 'start_time="$(date -u +%s.%N)"\n'
        script += "# Execute command\n"
        script += " ".join(command) + "\n\n"
        script += 'end_time="$(date -u +%s.%N)"\n'
        script += 'elapsed="$(bc <<<"$end_time-$start_time")"\n'
        script += 'echo "Total of $elapsed seconds elapsed for process"\n'
        
        script += "date\n"
        
        return script
    
    def submit_job(self, script_path: Path) -> str:
        """Execute script as a local process."""
        try:
            # Create unique job ID
            job_id = f"local_{int(time.time() * 1000)}"
            
            # Get output path
            output_path = script_path.parent / "out_local"
            error_path = script_path.parent / "err_local"
            
            # Start process
            with open(output_path, 'w') as outfile, open(error_path, 'w') as errfile:
                process = subprocess.Popen(
                    ["/bin/bash", str(script_path)],
                    stdout=outfile,
                    stderr=errfile,
                    cwd=script_path.parent
                )
            
            self.processes[job_id] = process
            logger.debug(f"Started local process {process.pid} as {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start local job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """Check if local process is still running."""
        if job_id not in self.processes:
            return JobStatus.UNKNOWN
        
        process = self.processes[job_id]
        returncode = process.poll()
        
        if returncode is None:
            return JobStatus.RUNNING
        elif returncode == 0:
            return JobStatus.COMPLETED
        else:
            return JobStatus.FAILED
    
    def cancel_job(self, job_id: str) -> bool:
        """Terminate local process."""
        if job_id not in self.processes:
            return False
        
        try:
            process = self.processes[job_id]
            process.send_signal(signal.SIGTERM)
            time.sleep(1)
            
            if process.poll() is None:
                process.kill()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def wait_for_completion(
        self,
        job_id: str,
        timeout: Optional[int] = None
    ) -> JobStatus:
        """Wait for local process to complete."""
        if job_id not in self.processes:
            return JobStatus.UNKNOWN
        
        try:
            process = self.processes[job_id]
            returncode = process.wait(timeout=timeout)
            
            if returncode == 0:
                return JobStatus.COMPLETED
            else:
                return JobStatus.FAILED
                
        except subprocess.TimeoutExpired:
            return JobStatus.TIMEOUT
        except Exception as e:
            logger.error(f"Error waiting for job {job_id}: {e}")
            return JobStatus.FAILED
