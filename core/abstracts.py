"""
Abstract base classes defining the plugin interfaces.
"""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from .config import JobConfig, ResourceConfig
from .types import JobStatus


logger = logging.getLogger(__name__)


class SchedulerInterface(ABC):
    """Abstract interface for job schedulers."""
    
    def __init__(self, options: Optional[Dict] = None):
        self.options = options or {}
    
    @abstractmethod
    def generate_job_script(
        self,
        job_config: JobConfig,
        resource_config: ResourceConfig,
        command: List[str],
        env_setup: List[str]
    ) -> str:
        """Generate a job submission script."""
        pass
    
    @abstractmethod
    def submit_job(self, script_path: Path) -> str:
        """Submit a job and return job ID."""
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> JobStatus:
        """Query the status of a job."""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        pass
    
    @abstractmethod
    def wait_for_completion(
        self,
        job_id: str,
        timeout: Optional[int] = None
    ) -> JobStatus:
        """Wait for job completion."""
        pass


class LauncherInterface(ABC):
    """Abstract interface for MPI launchers."""
    
    def __init__(self, options: Optional[Dict] = None):
        self.options = options or {}
    
    @abstractmethod
    def generate_launch_command(
        self,
        job_config: JobConfig,
        executable: List[str],
        resource_config: ResourceConfig
    ) -> List[str]:
        """Generate the MPI launch command."""
        pass
    
    @abstractmethod
    def supports_gpu_binding(self) -> bool:
        """Check if launcher supports GPU binding."""
        pass


class ModuleSystemInterface(ABC):
    """Abstract interface for environment module systems."""
    
    def __init__(self, options: Optional[Dict] = None):
        self.options = options or {}
    
    @abstractmethod
    def generate_load_commands(self, modules: List[str]) -> List[str]:
        """Generate commands to load modules."""
        pass
    
    @abstractmethod
    def generate_unload_commands(self, modules: List[str]) -> List[str]:
        """Generate commands to unload modules."""
        pass
    
    @abstractmethod
    def list_available_modules(self, pattern: Optional[str] = None) -> List[str]:
        """List available modules."""
        pass
    
    @abstractmethod
    def is_module_available(self, module: str) -> bool:
        """Check if a module is available."""
        pass


class BuildSystemInterface(ABC):
    """Abstract interface for build systems."""
    
    def __init__(self, options: Optional[Dict] = None):
        self.options = options or {}
    
    @abstractmethod
    def configure(
        self,
        source_dir: Path,
        build_dir: Path,
        flags: Optional[Dict[str, str]] = None
    ) -> bool:
        """Configure the build system."""
        pass
    
    @abstractmethod
    def build(
        self,
        build_dir: Path,
        parallel_jobs: int = 1
    ) -> bool:
        """Execute the build."""
        pass
    
    @abstractmethod
    def install(
        self,
        build_dir: Path,
        install_dir: Path
    ) -> bool:
        """Install the built artifacts."""
        pass
    
    @abstractmethod
    def clean(self, build_dir: Path) -> bool:
        """Clean build artifacts."""
        pass


class ResultParserInterface(ABC):
    """Abstract interface for parsing job results."""
    
    @abstractmethod
    def parse_output(self, output_file: Path) -> Dict:
        """Parse job output and extract metrics."""
        pass
    
    @abstractmethod
    def extract_timing(self, output_file: Path) -> Optional[float]:
        """Extract timing information from output."""
        pass
    
    @abstractmethod
    def extract_performance_metrics(self, output_file: Path) -> Dict:
        """Extract performance metrics."""
        pass


class DefaultResultParser(ResultParserInterface):
    """Enhanced result parser for common benchmark outputs with comprehensive metrics extraction."""
    
    def __init__(self):
        self.time_patterns = [
            r'(?:Time|Wall\s+time|Runtime|Elapsed):\s*(\d+(?:\.\d+)?)',
            r'Total time: (\d+(?:\.\d+)?) seconds',
            r'Performance: .* time = (\d+(?:\.\d+)?)',
            r'Total of (\d+(?:\.\d+)?) seconds elapsed for process',
            r'Wall clock time: (\d+(?:\.\d+)?)',
            r'Execution time: (\d+(?:\.\d+)?)',
            r'Time elapsed: (\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*seconds\s*total'
        ]
        
        self.performance_patterns = {
            'gflops': [
                r'(?:GFLOPS|GFlop/s|GFLOP/s):\s*(\d+(?:\.\d+)?)',
                r'Performance:\s*(\d+(?:\.\d+)?)\s*GFLOPS',
                r'(\d+(?:\.\d+)?)\s*GFLOPS'
            ],
            'mflops': [
                r'(?:MFLOPS|MFlop/s|MFLOP/s):\s*(\d+(?:\.\d+)?)',
                r'Performance:\s*(\d+(?:\.\d+)?)\s*MFLOPS',
                r'(\d+(?:\.\d+)?)\s*MFLOPS'
            ],
            'tflops': [
                r'(?:TFLOPS|TFlop/s|TFLOP/s):\s*(\d+(?:\.\d+)?)',
                r'Performance:\s*(\d+(?:\.\d+)?)\s*TFLOPS',
                r'(\d+(?:\.\d+)?)\s*TFLOPS'
            ]
        }
        
        self.memory_patterns = [
            r'Peak memory:\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB)',
            r'Memory usage:\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB)',
            r'RAM:\s*(\d+(?:\.\d+)?)\s*(GB|MB|KB)',
            r'(\d+(?:\.\d+)?)\s*(GB|MB|KB)\s*memory'
        ]
        
        self.error_patterns = [
            r'ERROR',
            r'FATAL',
            r'FAILED',
            r'Exception',
            r'Segmentation fault',
            r'Aborted',
            r'Killed'
        ]
    
    def parse_output(self, output_file: Path) -> Dict:
        """Parse output file and extract comprehensive metrics."""
        try:
            content = output_file.read_text()
            metrics = {}
            
            # Extract timing information
            wall_time = self._extract_timing(content)
            if wall_time is not None:
                metrics['wall_time'] = wall_time
            
            # Extract performance metrics
            performance_metrics = self._extract_performance_metrics(content)
            metrics.update(performance_metrics)
            
            # Extract memory usage
            memory_usage = self._extract_memory_usage(content)
            if memory_usage is not None:
                metrics['memory_usage'] = memory_usage
            
            # Extract error information
            errors = self._extract_errors(content)
            if errors:
                metrics['errors'] = errors
            
            # Extract scaling information
            scaling_info = self._extract_scaling_info(content)
            metrics.update(scaling_info)
            
            # Extract application-specific metrics
            app_metrics = self._extract_application_metrics(content)
            metrics.update(app_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to parse {output_file}: {e}")
            return {}
    
    def _extract_timing(self, content: str) -> Optional[float]:
        """Extract wall time from content."""
        for pattern in self.time_patterns:
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_performance_metrics(self, content: str) -> Dict[str, float]:
        """Extract performance metrics from content."""
        metrics = {}
        
        for metric_type, patterns in self.performance_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.I | re.M)
                if match:
                    try:
                        value = float(match.group(1))
                        metrics[f'performance_{metric_type}'] = value
                        break
                    except ValueError:
                        continue
        
        return metrics
    
    def _extract_memory_usage(self, content: str) -> Optional[float]:
        """Extract memory usage in GB."""
        for pattern in self.memory_patterns:
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2).upper()
                    
                    # Convert to GB
                    if unit == 'KB':
                        return value / (1024 * 1024)
                    elif unit == 'MB':
                        return value / 1024
                    elif unit == 'GB':
                        return value
                    elif unit == 'TB':
                        return value * 1024
                    
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_errors(self, content: str) -> List[str]:
        """Extract error messages from content."""
        errors = []
        
        for pattern in self.error_patterns:
            matches = re.findall(pattern, content, re.I | re.M)
            errors.extend(matches)
        
        return list(set(errors))  # Remove duplicates
    
    def _extract_scaling_info(self, content: str) -> Dict[str, Any]:
        """Extract scaling-related information."""
        info = {}
        
        # Extract processor count
        proc_patterns = [
            r'(\d+)\s*processors?',
            r'(\d+)\s*MPI\s*processes?',
            r'(\d+)\s*cores?',
            r'Running on (\d+)\s*nodes?'
        ]
        
        for pattern in proc_patterns:
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    info['num_processors'] = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract problem size
        size_patterns = [
            r'Problem size:\s*(\d+(?:\.\d+)?)',
            r'Grid size:\s*(\d+(?:\.\d+)?)',
            r'Cells:\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*cells?'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    info['problem_size'] = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return info
    
    def _extract_application_metrics(self, content: str) -> Dict[str, Any]:
        """Extract application-specific metrics."""
        metrics = {}
        
        # iPIC3D specific patterns
        ipic_patterns = {
            'particles_per_cell': r'particles per cell:\s*(\d+(?:\.\d+)?)',
            'time_steps': r'time steps:\s*(\d+)',
            'domain_size': r'domain size:\s*(\d+(?:\.\d+)?)',
            'cell_size': r'cell size:\s*(\d+(?:\.\d+)?)',
            'dt': r'dt\s*=\s*(\d+(?:\.\d+)?)',
            'dx': r'dx\s*=\s*(\d+(?:\.\d+)?)',
            'dy': r'dy\s*=\s*(\d+(?:\.\d+)?)',
            'dz': r'dz\s*=\s*(\d+(?:\.\d+)?)'
        }
        
        for key, pattern in ipic_patterns.items():
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    metrics[key] = float(match.group(1))
                except ValueError:
                    try:
                        metrics[key] = int(match.group(1))
                    except ValueError:
                        continue
        
        # General scientific computing patterns
        general_patterns = {
            'iterations': r'(\d+)\s*iterations?',
            'convergence': r'converged after (\d+)',
            'residual': r'residual:\s*(\d+(?:\.\d+)?[eE]?[+-]?\d*)',
            'tolerance': r'tolerance:\s*(\d+(?:\.\d+)?[eE]?[+-]?\d*)'
        }
        
        for key, pattern in general_patterns.items():
            match = re.search(pattern, content, re.I | re.M)
            if match:
                try:
                    metrics[key] = float(match.group(1))
                except ValueError:
                    try:
                        metrics[key] = int(match.group(1))
                    except ValueError:
                        continue
        
        return metrics
    
    def extract_timing(self, output_file: Path) -> Optional[float]:
        """Extract timing information from output file."""
        try:
            content = output_file.read_text()
            return self._extract_timing(content)
        except Exception as e:
            logger.error(f"Failed to extract timing from {output_file}: {e}")
            return None
    
    def extract_performance_metrics(self, output_file: Path) -> Dict:
        """Extract performance metrics from output file."""
        try:
            content = output_file.read_text()
            return self._extract_performance_metrics(content)
        except Exception as e:
            logger.error(f"Failed to extract performance metrics from {output_file}: {e}")
            return {}
    
    def extract_scaling_metrics(self, output_file: Path) -> Dict[str, Any]:
        """Extract scaling-specific metrics."""
        try:
            content = output_file.read_text()
            return self._extract_scaling_info(content)
        except Exception as e:
            logger.error(f"Failed to extract scaling metrics from {output_file}: {e}")
            return {}
    
    def extract_application_metrics(self, output_file: Path) -> Dict[str, Any]:
        """Extract application-specific metrics."""
        try:
            content = output_file.read_text()
            return self._extract_application_metrics(content)
        except Exception as e:
            logger.error(f"Failed to extract application metrics from {output_file}: {e}")
            return {}
    
    def is_successful(self, output_file: Path) -> bool:
        """Check if the job was successful based on output."""
        try:
            content = output_file.read_text()
            
            # Check for error patterns
            errors = self._extract_errors(content)
            if errors:
                return False
            
            # Check for success indicators
            success_patterns = [
                r'SUCCESS',
                r'completed successfully',
                r'finished successfully',
                r'normal termination',
                r'job completed'
            ]
            
            for pattern in success_patterns:
                if re.search(pattern, content, re.I | re.M):
                    return True
            
            # If we have timing information, consider it successful
            if self._extract_timing(content) is not None:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check success status of {output_file}: {e}")
            return False
