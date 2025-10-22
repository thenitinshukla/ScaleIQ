"""Run directory helpers for test artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = PROJECT_ROOT / "runs"


def _timestamp(ts: datetime | None = None) -> str:
    return (ts or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")


@dataclass
class RunPaths:
    run_id: str
    root: Path = RUNS_ROOT

    @classmethod
    def create(cls, suffix: str | None = None) -> "RunPaths":
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        keep = RUNS_ROOT / ".keep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

        attempts = 0
        while attempts < 5:
            run_id = _timestamp()
            if suffix:
                run_id = f"{run_id}-{suffix}"
            run_dir = RUNS_ROOT / run_id
            try:
                run_dir.mkdir()
                return cls(run_id=run_id)
            except FileExistsError:
                attempts += 1
        raise RuntimeError("Unable to allocate unique run directory")

    @property
    def run_dir(self) -> Path:
        return self.root / self.run_id

    @property
    def env_file(self) -> Path:
        return self.run_dir / "env.json"

    @property
    def events_log(self) -> Path:
        return self.run_dir / "events.jsonl"

    def ensure_subdir(self, name: str) -> Path:
        subdir = self.run_dir / name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def append_event(self, record: dict) -> None:
        entry = dict(record)
        entry.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        with self.events_log.open("a", encoding="utf-8") as handle:
            json.dump(entry, handle, separators=(",", ":"))
            handle.write("\n")
