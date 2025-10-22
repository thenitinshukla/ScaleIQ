#!/usr/bin/env python3
"""Harness per la suite 05 (build Make)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.build_make import MakeBuilder
from utils.paths import RunPaths

EXPECTED_ARTIFACTS = PROJECT_ROOT / "tests/05_build_make/expected/artifact_manifest.json"
EXPECTED_METRICS = PROJECT_ROOT / "tests/05_build_make/expected/metrics_template.json"

MAKEFILE_CONTENT = """
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17
LDFLAGS ?=
TARGET := solver
LIB := libsolver.a
OBJS := solver.o main.o

all: $(TARGET) $(LIB)

$(TARGET): solver.o main.o
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

$(LIB): solver.o
	ar rcs $@ $^

solver.o: solver.cpp solver.hpp
	$(CXX) $(CXXFLAGS) -c solver.cpp -o solver.o

main.o: main.cpp solver.hpp
	$(CXX) $(CXXFLAGS) -c main.cpp -o main.o

clean:
	rm -f $(TARGET) $(LIB) $(OBJS)

.PHONY: all clean
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

SOLVER_HPP = """
#pragma once

int solve();
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
    src_files = {
        "Makefile": MAKEFILE_CONTENT,
        "solver.cpp": SOLVER_CPP,
        "solver.hpp": SOLVER_HPP,
        "main.cpp": MAIN_CPP,
    }
    target.mkdir(parents=True, exist_ok=True)
    for name, content in src_files.items():
        (target / name).write_text(content + "\n", encoding="utf-8")


def write_log(path: Path, result) -> None:
    path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")


def main() -> int:
    run_paths = RunPaths.create()
    workspace = run_paths.ensure_subdir("workspace")
    project_dir = workspace / "make_project"
    scaffold_project(project_dir)

    builder = MakeBuilder()
    jobs = min(os.cpu_count() or 2, 4)

    build_start = time.perf_counter()
    build_result = builder.run(project_dir, jobs=jobs)
    build_duration = time.perf_counter() - build_start
    if build_result.returncode != 0:
        raise RuntimeError(f"Make build failed: {build_result.stderr}")

    log_path = run_paths.run_dir / "make_build.log"
    write_log(log_path, build_result)
    run_paths.append_event(
        {
            "step": "T-0501-make-j",
            "action": "make_build",
            "log_path": str(log_path.relative_to(PROJECT_ROOT)),
            "jobs": jobs,
            "duration_sec": round(build_duration, 3),
        }
    )

    artifacts_dir = run_paths.ensure_subdir("artifacts")
    artifacts = builder.collect_artifacts(project_dir, artifacts_dir)
    manifest_path = run_paths.run_dir / "artifact_manifest.json"
    run_paths.write_json(manifest_path, {"artifacts": artifacts})

    expected_names = set()
    if EXPECTED_ARTIFACTS.exists():
        expected_manifest = json.loads(EXPECTED_ARTIFACTS.read_text(encoding="utf-8"))
        expected_names = {entry["path"] for entry in expected_manifest.get("artifacts", [])}
    produced_names = {entry["name"] for entry in artifacts}

    run_paths.append_event(
        {
            "step": "T-0501-make-j",
            "action": "collect_artifacts",
            "artifact_manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
            "artifacts_found": sorted(produced_names),
            "covers_expected": expected_names.issubset(produced_names) if expected_names else True,
        }
    )

    metrics = {
        "make": {
            "duration_sec": round(build_duration, 3),
            "jobs": jobs,
            "commands": ["make -j{} all".format(jobs)],
        }
    }
    metrics_path = run_paths.run_dir / "metrics.json"
    run_paths.write_json(metrics_path, metrics)

    print(f"[build_make] Run artifacts stored in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
