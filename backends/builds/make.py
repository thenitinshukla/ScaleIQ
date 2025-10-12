"""
Standard Makefile backend.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict

from core.abstracts import BuildSystemInterface


logger = logging.getLogger(__name__)


class MakeBackend(BuildSystemInterface):
    def configure(self, source_dir: Path, build_dir: Path, flags: Optional[Dict[str, str]] = None) -> bool:
        logger.info("Make: No configure step")
        return True
    
    def build(self, build_dir: Path, parallel_jobs: int = 1) -> bool:
        try:
            cmd = ["make", f"-j{parallel_jobs}"]
            logger.info(f"Building: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, check=True)
            logger.info("Build OK")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Build failed: {e.stderr}")
            return False
    
    def install(self, build_dir: Path, install_dir: Path) -> bool:
        try:
            cmd = ["make", "install", f"DESTDIR={install_dir}"]
            logger.info(f"Installing: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, check=True)
            logger.info("Install OK")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Install failed: {e.stderr}")
            return False
    
    def clean(self, build_dir: Path) -> bool:
        try:
            subprocess.run(["make", "clean"], cwd=build_dir, capture_output=True, check=True)
            logger.info("Clean OK")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Clean failed: {e.stderr}")
            return False
