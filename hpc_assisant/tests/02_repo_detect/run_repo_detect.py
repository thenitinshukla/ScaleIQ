"""Harness for suite 02 (repository detection)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.paths import RunPaths
from utils.repo import CloneResult, clone, detect_buildsystem, save_clone_metadata

DATA_DIR = Path(__file__).resolve().parent / "data"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def load_repo_descriptor() -> dict:
    with (DATA_DIR / "repo_target.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def load_expected_detection() -> dict:
    path = EXPECTED_DIR / "detection.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ensure_clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def main() -> int:
    descriptor = load_repo_descriptor()
    run_paths = RunPaths.create()
    workspace = run_paths.ensure_subdir("workspace")

    repo_url = descriptor["url"]
    ref = descriptor.get("ref") or None
    clone_result: CloneResult
    try:
        clone_result = clone(repo_url, workspace, ref=ref, depth=1)
    except Exception as exc:  # pragma: no cover - immediate failure path
        run_paths.append_event(
            {
                "step": "T-0201-git-clone",
                "action": "clone",
                "url": repo_url,
                "status": "error",
                "error": str(exc),
            }
        )
        print(f"[repo_detect] ERROR cloning repo: {exc}", file=sys.stderr)
        return 1

    metadata_path = run_paths.run_dir / "repo_metadata.json"
    save_clone_metadata(clone_result, metadata_path)
    run_paths.append_event(
        {
            "step": "T-0201-git-clone",
            "action": "clone",
            "url": repo_url,
            "ref": clone_result.ref,
            "commit": clone_result.sha,
            "metadata_path": str(metadata_path.relative_to(PROJECT_ROOT)),
        }
    )

    detection = detect_buildsystem(clone_result.path)
    detection_path = run_paths.run_dir / "detection.json"
    run_paths.write_json(detection_path, detection)

    expected_detection = load_expected_detection()
    matches_expected = bool(expected_detection) and detection["type"] == expected_detection.get("type")
    run_paths.append_event(
        {
            "step": "T-0202-detect-buildsystem",
            "action": "detect_buildsystem",
            "detection_path": str(detection_path.relative_to(PROJECT_ROOT)),
            "type": detection["type"],
            "languages": [entry["name"] for entry in detection.get("languages", [])],
            "matches_expected_type": matches_expected,
        }
    )

    print(f"[repo_detect] Run artifacts stored in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
