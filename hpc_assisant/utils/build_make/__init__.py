"""Utilities for invoking GNU Make builds."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass
class MakeResult:
    command: list[str]
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str


class MakeBuilder:
    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self.env = dict(env) if env is not None else None

    def run(self, path: Path, target: str | None = None, jobs: int | None = None, extra_args: Iterable[str] | None = None) -> MakeResult:
        cmd = ["make"]
        if jobs:
            cmd.extend(["-j", str(jobs)])
        if target:
            cmd.append(target)
        if extra_args:
            cmd.extend(extra_args)

        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=str(path),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        duration = time.perf_counter() - start
        return MakeResult(
            command=cmd,
            returncode=proc.returncode,
            duration_sec=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def collect_artifacts(self, build_dir: Path, destination: Path) -> list[dict]:
        destination.mkdir(parents=True, exist_ok=True)
        artifacts: list[dict] = []
        library_suffixes = {".a", ".so", ".dylib"}
        for file_path in build_dir.iterdir():
            if not file_path.is_file():
                continue
            is_executable = os.access(file_path, os.X_OK)
            if file_path.suffix in library_suffixes or is_executable:
                dest_file = destination / file_path.name
                shutil.copy2(file_path, dest_file)
                artifacts.append(
                    {
                        "name": file_path.name,
                        "original_path": str(file_path),
                        "copied_path": str(dest_file),
                        "sha256": self._sha256(dest_file),
                    }
                )
        return artifacts

    @staticmethod
    def _sha256(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
