"""Repository management utilities for cloning and build-system detection."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "C": (".c",),
    "C++": (".cc", ".cpp", ".cxx", ".c++", ".hpp", ".hh", ".hxx"),
    "Fortran": (".f", ".f90", ".f95", ".f03", ".f08"),
    "CUDA": (".cu", ".cuh"),
    "Python": (".py",),
    "HIP": (".hip", ".hip.cpp"),
}


@dataclass
class CloneResult:
    path: Path
    sha: str
    url: str
    ref: str | None = None


def _run_git(args: Iterable[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
    )


def clone(
    url: str,
    dest_root: Path,
    ref: str | None = None,
    depth: int = 1,
    recurse_submodules: bool = True,
) -> CloneResult:
    dest_root.mkdir(parents=True, exist_ok=True)
    repo_name = url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    destination = dest_root / repo_name
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    clone_args = ["clone"]
    if depth:
        clone_args.extend(["--depth", str(depth)])
    if ref:
        clone_args.extend(["--branch", ref])
    clone_args.extend([url, str(destination)])
    _run_git(clone_args)

    if recurse_submodules:
        _run_git(["submodule", "update", "--init", "--recursive"], cwd=destination)

    sha = _run_git(["rev-parse", "HEAD"], cwd=destination).stdout.strip()
    checked_out_ref = ref or _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=destination).stdout.strip()

    return CloneResult(path=destination, sha=sha, url=url, ref=checked_out_ref)


def detect_buildsystem(path: Path) -> dict:
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {path}")

    evidence: list[str] = []
    build_type = "unknown"
    cmake_file = path / "CMakeLists.txt"
    makefile = None
    for candidate in ("Makefile", "makefile"):
        candidate_path = path / candidate
        if candidate_path.exists():
            makefile = candidate_path
            break

    if cmake_file.exists():
        build_type = "cmake"
        evidence.append(str(cmake_file.relative_to(path)))
    elif makefile:
        build_type = "make"
        evidence.append(str(makefile.relative_to(path)))

    language_counts: dict[str, int] = {}
    total_files = 0
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if suffix in extensions:
                language_counts[language] = language_counts.get(language, 0) + 1
                total_files += 1
                break

    languages = []
    if total_files:
        for language, count in sorted(language_counts.items(), key=lambda item: item[1], reverse=True):
            percentage = int(round((count / total_files) * 100))
            languages.append({"name": language, "percentage": percentage})

    notes = ""
    if build_type == "unknown":
        notes = "No known build-system indicator files were found."

    return {
        "path": str(path),
        "type": build_type,
        "languages": languages,
        "evidence": evidence,
        "notes": notes,
    }


def save_clone_metadata(result: CloneResult, destination: Path) -> None:
    payload = {
        "url": result.url,
        "ref": result.ref,
        "commit": result.sha,
        "path": str(result.path),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
