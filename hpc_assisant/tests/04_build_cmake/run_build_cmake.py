#!/usr/bin/env python3
"""Harness for suite 04 (CMake build)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.build_cmake import CMakeBuilder
from utils.paths import RunPaths

EXPECTED_ARTIFACTS = PROJECT_ROOT / "tests/04_build_cmake/expected/artifact_manifest.json"


CMAKELISTS_CONTENT = """
cmake_minimum_required(VERSION 3.15)
project(hpc_cmake_suite LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(solver_lib STATIC src/solver.cpp)
set_target_properties(solver_lib PROPERTIES OUTPUT_NAME solver)
target_include_directories(solver_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(solver_driver src/main.cpp)
set_target_properties(solver_driver PROPERTIES OUTPUT_NAME solver)
target_link_libraries(solver_driver PRIVATE solver_lib)
""".strip()

SOLVER_HPP = """
#pragma once

int solve();
""".strip()

SOLVER_CPP = """
#include "solver.hpp"

int solve() {
    int result = 0;
    for (int i = 0; i < 100; ++i) {
        result += i;
    }
    return result;
}
""".strip()

MAIN_CPP = """
#include <iostream>
#include "solver.hpp"

int main() {
    std::cout << "solver result: " << solve() << std::endl;
    return 0;
}
""".strip()


def scaffold_project(target: Path) -> None:
    src_dir = target / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (target / "CMakeLists.txt").write_text(CMAKELISTS_CONTENT + "\n", encoding="utf-8")
    (src_dir / "solver.hpp").write_text(SOLVER_HPP + "\n", encoding="utf-8")
    (src_dir / "solver.cpp").write_text(SOLVER_CPP + "\n", encoding="utf-8")
    (src_dir / "main.cpp").write_text(MAIN_CPP + "\n", encoding="utf-8")


def write_log(path: Path, result) -> None:
    path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")


def main() -> int:
    run_paths = RunPaths.create()
    workspace = run_paths.ensure_subdir("workspace")
    project_dir = workspace / "cmake_project"
    scaffold_project(project_dir)

    builder = CMakeBuilder()
    build_dir = project_dir / "build"

    configure_start = time.perf_counter()
    configure_result = builder.configure(
        source=project_dir,
        build=build_dir,
        flags=["-DCMAKE_BUILD_TYPE=Release"],
    )
    configure_duration = time.perf_counter() - configure_start
    config_log_path = run_paths.run_dir / "cmake_config.log"
    write_log(config_log_path, configure_result)
    run_paths.append_event(
        {
            "step": "T-0401-configure",
            "action": "cmake_configure",
            "log_path": str(config_log_path.relative_to(PROJECT_ROOT)),
            "duration_sec": round(configure_duration, 3),
        }
    )

    build_start = time.perf_counter()
    build_result = builder.build(build=build_dir, parallel=os.cpu_count() or 2)
    build_duration = time.perf_counter() - build_start
    build_log_path = run_paths.run_dir / "cmake_build.log"
    write_log(build_log_path, build_result)
    run_paths.append_event(
        {
            "step": "T-0402-build",
            "action": "cmake_build",
            "log_path": str(build_log_path.relative_to(PROJECT_ROOT)),
            "duration_sec": round(build_duration, 3),
        }
    )

    artifacts_dir = run_paths.ensure_subdir("artifacts")
    artifacts = builder.collect_artifacts(build_dir, artifacts_dir)
    artifact_manifest_path = run_paths.run_dir / "artifact_manifest.json"
    run_paths.write_json(artifact_manifest_path, {"artifacts": artifacts})

    expected_names = set()
    if EXPECTED_ARTIFACTS.exists():
        expected_manifest = json.loads(EXPECTED_ARTIFACTS.read_text(encoding="utf-8"))
        expected_names = {entry["path"] for entry in expected_manifest.get("artifacts", [])}
    produced_names = {entry["name"] for entry in artifacts}
    run_paths.append_event(
        {
            "step": "T-0402-build",
            "action": "collect_artifacts",
            "artifact_manifest": str(artifact_manifest_path.relative_to(PROJECT_ROOT)),
            "artifacts_found": sorted(produced_names),
            "covers_expected": expected_names.issubset(produced_names) if expected_names else True,
        }
    )

    metrics_path = run_paths.run_dir / "metrics.json"
    run_paths.write_json(
        metrics_path,
        {
            "configure": {
                "duration_sec": round(configure_duration, 3),
            },
            "build": {
                "duration_sec": round(build_duration, 3),
                "parallel": os.cpu_count() or 2,
            },
        },
    )

    print(f"[build_cmake] Run artifacts stored in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
