"""Bootstrap harness to execute suite 00 tests (T-0001, T-0002)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ConfigProvider
from utils.paths import RunPaths


def iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def layout_snapshot() -> dict:
    expected_dirs = ["runs", "tests", "utils"]
    snapshot: dict[str, dict[str, bool]] = {}
    for name in expected_dirs:
        path = PROJECT_ROOT / name
        snapshot[name] = {"exists": path.exists(), "is_dir": path.is_dir()}
    runs_keep = PROJECT_ROOT / "runs" / ".keep"
    snapshot["runs/.keep"] = {"exists": runs_keep.exists(), "is_file": runs_keep.is_file()}
    return snapshot


def main() -> int:
    try:
        config = ConfigProvider()
        values = config.as_dict()
        masked = config.masked()
    except Exception as exc:  # pragma: no cover - immediate failure path
        print(f"[bootstrap] ERROR: {exc}", file=sys.stderr)
        return 1

    run_paths = RunPaths.create()

    env_payload = {
        **masked,
        "_metadata": {
            "generated_at": iso_utc(),
            "source": str(config.env_path),
            "masking_strategy": "pattern_based",
        },
    }
    run_paths.write_json(run_paths.env_file, env_payload)
    run_paths.append_event(
        {
            "step": "T-0001-env-file",
            "action": "write_env_json",
            "env_path": str(run_paths.env_file.relative_to(PROJECT_ROOT)),
            "keys_dumped": sorted(masked.keys()),
        }
    )

    layout = layout_snapshot()
    layout_path = run_paths.run_dir / "layout_check.json"
    run_paths.write_json(layout_path, layout)
    issues = {key: details for key, details in layout.items() if not details.get("exists")}
    run_paths.append_event(
        {
            "step": "T-0002-layout",
            "action": "layout_snapshot",
            "layout_path": str(layout_path.relative_to(PROJECT_ROOT)),
            "issues": issues,
        }
    )

    print(f"[bootstrap] Run artifacts stored in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
