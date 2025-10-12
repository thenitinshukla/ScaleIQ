"""
Enhanced CMake backend with robust environment setup and dependency handling.
"""

import subprocess
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List

from core.abstracts import BuildSystemInterface


logger = logging.getLogger(__name__)


class CMakeBackend(BuildSystemInterface):
    """Enhanced CMake build system with environment and dependency support."""
    
    def __init__(self, options: Optional[Dict] = None):
        super().__init__(options)
        self.cmake_min_version = "3.10"
        self.build_type = "Release"
    
    def configure(self, source_dir: Path, build_dir: Path, flags: Optional[Dict[str, str]] = None) -> bool:
        """Configure CMake project with enhanced environment setup."""
        try:
            # Ensure build directory exists
            build_dir.mkdir(parents=True, exist_ok=True)
            
            # Check CMake availability
            if not self._check_cmake_available():
                logger.error("CMake not found in PATH")
                return False
            
            # Prepare CMake command
            cmd = ["cmake", str(source_dir)]
            
            # Add standard flags
            standard_flags = {
                "CMAKE_BUILD_TYPE": self.build_type,
                "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
                "BUILD_SHARED_LIBS": "OFF"
            }
            
            # Merge with provided flags
            effective_flags = {**standard_flags, **(flags or {})}
            
            # Add compiler flags from environment
            effective_flags.update(self._get_compiler_flags_from_env())
            
            # Add dependency paths
            effective_flags.update(self._get_dependency_paths())
            
            # Convert flags to CMake arguments
            for key, value in effective_flags.items():
                cmd.extend([f"-D{key}={value}"])
            
            logger.info(f"Configuring CMake: {' '.join(cmd)}")
            logger.debug(f"Effective flags: {effective_flags}")
            
            # Run CMake configuration
            result = subprocess.run(
                cmd, 
                cwd=build_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True,
                env=self._get_build_environment()
            )
            
            logger.info("CMake configuration successful")
            logger.debug(f"CMake output: {result.stdout.decode()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"CMake configuration failed: {e.stderr.decode()}")
            logger.debug(f"CMake stdout: {e.stdout.decode()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during CMake configuration: {e}")
            return False
    
    def build(self, build_dir: Path, parallel_jobs: int = 1) -> bool:
        """Build the project with enhanced error handling."""
        try:
            # Validate build directory
            if not build_dir.exists():
                logger.error(f"Build directory does not exist: {build_dir}")
                return False
            
            # Check if CMakeCache.txt exists
            cmake_cache = build_dir / "CMakeCache.txt"
            if not cmake_cache.exists():
                logger.error("CMakeCache.txt not found - project not configured")
                return False
            
            # Prepare build command
            cmd = ["cmake", "--build", ".", "--parallel", str(parallel_jobs)]
            
            # Add verbose output if debug logging
            if logger.isEnabledFor(logging.DEBUG):
                cmd.append("--verbose")
            
            logger.info(f"Building project: {' '.join(cmd)}")
            
            # Run build
            result = subprocess.run(
                cmd,
                cwd=build_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                env=self._get_build_environment()
            )
            
            logger.info("Build successful")
            logger.debug(f"Build output: {result.stdout.decode()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Build failed: {e.stderr.decode()}")
            logger.debug(f"Build stdout: {e.stdout.decode()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during build: {e}")
            return False
    
    def install(self, build_dir: Path, install_dir: Path) -> bool:
        """Install the built project."""
        try:
            # Ensure install directory exists
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if build was successful
            if not self._check_build_success(build_dir):
                logger.error("Build not successful - cannot install")
                return False
            
            # Prepare install command
            cmd = ["cmake", "--install", ".", "--prefix", str(install_dir)]
            
            logger.info(f"Installing project: {' '.join(cmd)}")
            
            # Run install
            result = subprocess.run(
                cmd,
                cwd=build_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                env=self._get_build_environment()
            )
            
            logger.info("Installation successful")
            logger.debug(f"Install output: {result.stdout.decode()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation failed: {e.stderr.decode()}")
            logger.debug(f"Install stdout: {e.stdout.decode()}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during installation: {e}")
            return False
    
    def clean(self, build_dir: Path) -> bool:
        """Clean build artifacts."""
        try:
            if not build_dir.exists():
                logger.warning(f"Build directory does not exist: {build_dir}")
                return True
            
            # Try CMake clean first
            try:
                result = subprocess.run(
                    ["cmake", "--build", ".", "--target", "clean"],
                    cwd=build_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                logger.info("CMake clean successful")
                return True
            except subprocess.CalledProcessError:
                logger.warning("CMake clean failed, removing build directory")
            
            # Fallback: remove build directory
            shutil.rmtree(build_dir)
            logger.info("Build directory removed")
            return True
            
        except Exception as e:
            logger.error(f"Clean failed: {e}")
            return False
    
    def _check_cmake_available(self):
        """Check if CMake is available."""
        try:
            result = subprocess.run(
                ["cmake", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            version_line = result.stdout.decode().split('\n')[0]
            logger.debug(f"CMake version: {version_line}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _get_compiler_flags_from_env(self) -> Dict[str, str]:
        """Extract compiler flags from environment variables."""
        flags = {}
        
        # Check for MPI compilers
        if os.environ.get('CC'):
            flags['CMAKE_C_COMPILER'] = os.environ['CC']
        elif shutil.which('mpicc'):
            flags['CMAKE_C_COMPILER'] = 'mpicc'
        
        if os.environ.get('CXX'):
            flags['CMAKE_CXX_COMPILER'] = os.environ['CXX']
        elif shutil.which('mpicxx'):
            flags['CMAKE_CXX_COMPILER'] = 'mpicxx'
        
        if os.environ.get('FC'):
            flags['CMAKE_Fortran_COMPILER'] = os.environ['FC']
        elif shutil.which('mpifort'):
            flags['CMAKE_Fortran_COMPILER'] = 'mpifort'
        
        # Add compiler flags
        if os.environ.get('CFLAGS'):
            flags['CMAKE_C_FLAGS'] = os.environ['CFLAGS']
        
        if os.environ.get('CXXFLAGS'):
            flags['CMAKE_CXX_FLAGS'] = os.environ['CXXFLAGS']
        
        if os.environ.get('FFLAGS'):
            flags['CMAKE_Fortran_FLAGS'] = os.environ['FFLAGS']
        
        return flags
    
    def _get_dependency_paths(self) -> Dict[str, str]:
        """Get dependency paths from environment."""
        paths = {}
        
        # HDF5
        if os.environ.get('HDF5_ROOT'):
            paths['HDF5_ROOT'] = os.environ['HDF5_ROOT']
        elif os.environ.get('HDF5_DIR'):
            paths['HDF5_DIR'] = os.environ['HDF5_DIR']
        
        # MPI
        if os.environ.get('MPI_ROOT'):
            paths['MPI_ROOT'] = os.environ['MPI_ROOT']
        
        # OpenMP
        if os.environ.get('OMP_NUM_THREADS'):
            paths['OMP_NUM_THREADS'] = os.environ['OMP_NUM_THREADS']
        
        # CUDA
        if os.environ.get('CUDA_HOME'):
            paths['CUDA_HOME'] = os.environ['CUDA_HOME']
        elif os.environ.get('CUDA_ROOT'):
            paths['CUDA_ROOT'] = os.environ['CUDA_ROOT']
        
        return paths
    
    def _get_build_environment(self) -> Dict[str, str]:
        """Get build environment with necessary variables."""
        env = os.environ.copy()
        
        # Ensure parallel build
        if 'MAKEFLAGS' not in env:
            env['MAKEFLAGS'] = f'-j{os.cpu_count() or 1}'
        
        # Set compiler optimization
        if 'CFLAGS' not in env:
            env['CFLAGS'] = '-O3'
        if 'CXXFLAGS' not in env:
            env['CXXFLAGS'] = '-O3'
        
        return env
    
    def _check_build_success(self, build_dir: Path) -> bool:
        """Check if build was successful."""
        # Look for common build artifacts
        artifacts = [
            build_dir / "CMakeCache.txt",
            build_dir / "compile_commands.json"
        ]
        
        return any(artifact.exists() for artifact in artifacts)
