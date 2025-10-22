#!/usr/bin/env python3
"""Harness per la suite 06 (compile error triage)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.paths import RunPaths
from utils.triage import ErrorTriage, compile_rules

DATA_DIR = Path(__file__).resolve().parent / "data"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def load_log(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8")


def load_expected(name: str) -> dict:
    path = EXPECTED_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    run_paths = RunPaths.create()
    triage = ErrorTriage(compile_rules())

    cases = [
        ("T-0601-missing-header", "missing_header.log", "missing_header.json"),
        ("T-0602-invalid-flag", "invalid_flag.log", "invalid_flag.json"),
    ]

    for test_id, log_name, expected_name in cases:
        raw_log = load_log(log_name)
        outcome = triage.classify(raw_log)
        if outcome is None:
            raise RuntimeError(f"Nessuna regola ha classificato il log {log_name}")
        outcome["test_id"] = test_id

        result_path = run_paths.run_dir / f"{test_id}.json"
        run_paths.write_json(result_path, outcome)

        expected = load_expected(expected_name)
        matches_expected = bool(expected) and outcome["rule_id"] == expected.get("rule_id")
        run_paths.append_event(
            {
                "step": test_id,
                "action": "error_triage",
                "output": str(result_path.relative_to(PROJECT_ROOT)),
                "rule_id": outcome["rule_id"],
                "matches_expected": matches_expected,
            }
        )

    print(f"[error_triage_compile] Run artifacts in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
