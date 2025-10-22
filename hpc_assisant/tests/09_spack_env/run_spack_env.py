#!/usr/bin/env python3
"""Harness per la suite 09 (Spack environment)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.paths import RunPaths

MANIFEST_PATH = PROJECT_ROOT / "tests/09_spack_env/data/spack.yaml"
EXPECTED_PLAN = PROJECT_ROOT / "tests/09_spack_env/expected/spack_plan.json"
EXPECTED_DELTA = PROJECT_ROOT / "tests/09_spack_env/expected/env_delta.json"


def parse_manifest(path: Path) -> dict:
    specs: list[str] = []
    compilers: list[dict] = []
    section = None
    current_compiler: dict | None = None
    in_paths = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "specs:":
            section = "specs"
            continue
        if stripped == "compilers:":
            section = "compilers"
            continue

        if section == "specs" and stripped.startswith("- "):
            specs.append(stripped[2:])
            continue

        if section == "compilers":
            if stripped.startswith("- compiler"):
                current_compiler = {"paths": {}}
                compilers.append(current_compiler)
                in_paths = False
                continue
            if current_compiler is None:
                continue
            if stripped == "paths:":
                in_paths = True
                continue
            if in_paths and not any(stripped.startswith(f"{key}:") for key in ("cc", "cxx", "f77", "fc")):
                in_paths = False
            if stripped.startswith("-"):
                continue
            if ":" in stripped:
                key, value = [item.strip() for item in stripped.split(":", 1)]
                value = value.strip("\"'")
                if in_paths and key in ("cc", "cxx", "f77", "fc"):
                    current_compiler["paths"][key] = value
                else:
                    if key == "spec":
                        current_compiler["spec"] = value
                    elif key == "target":
                        current_compiler["target"] = value
                    elif key in {"operating_system", "os"}:
                        current_compiler["os"] = value
    return {"specs": specs, "compilers": compilers}


def load_expected(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    run_paths = RunPaths.create()
    plan = parse_manifest(MANIFEST_PATH)
    plan["manifest_path"] = str(MANIFEST_PATH.relative_to(PROJECT_ROOT))
    plan["spack_available"] = shutil.which("spack") is not None

    plan_path = run_paths.run_dir / "spack_plan.json"
    run_paths.write_json(plan_path, plan)

    expected_plan = load_expected(EXPECTED_PLAN)
    matches_plan = bool(expected_plan) and expected_plan.get("specs") == plan.get("specs")
    run_paths.append_event(
        {
            "step": "T-0901-detect-spack-yaml",
            "action": "plan_spack",
            "plan_path": str(plan_path.relative_to(PROJECT_ROOT)),
            "spack_available": plan["spack_available"],
            "matches_expected": matches_plan,
        }
    )

    if plan["spack_available"]:
        env_delta = {"status": "not_implemented", "message": "Attivazione reale non implementata"}
    else:
        env_delta = {
            "status": "spack_not_available",
            "message": "Comando spack non trovato; attivazione saltata.",
        }

    delta_path = run_paths.run_dir / "env_delta.json"
    run_paths.write_json(delta_path, env_delta)

    expected_delta = load_expected(EXPECTED_DELTA)
    matches_delta = bool(expected_delta) and expected_delta.get("status") == env_delta.get("status")
    run_paths.append_event(
        {
            "step": "T-0902-spack-activate",
            "action": "env_delta",
            "env_delta_path": str(delta_path.relative_to(PROJECT_ROOT)),
            "matches_expected": matches_delta,
        }
    )

    print(f"[spack_env] Run artifacts in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
