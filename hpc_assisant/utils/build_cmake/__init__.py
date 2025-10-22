"""Utilities for configuring and building CMake projects."""

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
class CommandResult:
    command: list[str]
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str


class CMakeBuilder:
    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self.env = dict(env) if env is not None else None

    def _run(self, args: Iterable[str], cwd: Path) -> CommandResult:
        cmd = list(args)
        start = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        duration = time.perf_counter() - start
        return CommandResult(
            command=cmd,
            returncode=proc.returncode,
            duration_sec=duration,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def configure(self, source: Path, build: Path, flags: list[str] | None = None) -> CommandResult:
        build.mkdir(parents=True, exist_ok=True)
        args = ["cmake", "-S", str(source), "-B", str(build)]
        if flags:
            args.extend(flags)
        result = self._run(args, cwd=source)
        if result.returncode != 0:
            raise RuntimeError(f"CMake configure failed: {result.stderr}")
        return result

    def build(self, build: Path, target: str | None = None, parallel: int | None = None) -> CommandResult:
        args = ["cmake", "--build", str(build)]
        if target:
            args.extend(["--target", target])
        if parallel:
            args.extend(["--parallel", str(parallel)])
        result = self._run(args, cwd=build)
        if result.returncode != 0:
            raise RuntimeError(f"CMake build failed: {result.stderr}")
        return result

    def collect_artifacts(self, build: Path, destination: Path) -> list[dict]:
        destination.mkdir(parents=True, exist_ok=True)
        artifacts: list[dict] = []
        for file_path in build.rglob("*"):
            if not file_path.is_file():
                continue
            if self._is_artifact(file_path):
                dest_file = destination / file_path.name
                shutil.copy2(file_path, dest_file)
                checksum = self._sha256(dest_file)
                artifacts.append(
                    {
                        "name": file_path.name,
                        "original_path": str(file_path),
                        "copied_path": str(dest_file),
                        "sha256": checksum,
                    }
                )
        return artifacts

    @staticmethod
    def _is_artifact(path: Path) -> bool:
        if "CMakeFiles" in path.parts:
            return False
        executable = os.access(path, os.X_OK)
        library_suffixes = {".a", ".so", ".dylib"}
        return executable or path.suffix in library_suffixes

    @staticmethod
    def _sha256(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
