"""Slurm runtime utilities for submission, monitoring, and log collection."""

from __future__ import annotations

import json
import os
import random
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Mapping, Sequence


def _now() -> datetime:
    return datetime.utcnow()


def _default_runner(command: Sequence[str], *, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, **(env or {})),
    )


def _parse_job_id(output: str) -> str:
    for token in output.split():
        if token.isdigit():
            return token
        if token.startswith(("JOBID=", "JobId=")):
            return token.split("=", 1)[1]
    raise ValueError(f"Unable to parse JobID from output: {output!r}")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_submission_paths(script: Path) -> tuple[Path | None, Path | None]:
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    for line in script.read_text(encoding="utf-8").splitlines():
        if line.startswith("#SBATCH -o"):
            stdout_path = Path(line.split(maxsplit=2)[-1])
        elif line.startswith("#SBATCH -e"):
            stderr_path = Path(line.split(maxsplit=2)[-1])
    return stdout_path, stderr_path


def _json_dump(data: Mapping[str, object], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


@dataclass
class SlurmRunner:
    """Submit and monitor Slurm jobs, with optional dry-run simulation."""

    policy: Mapping[str, object] = field(default_factory=dict)
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None
    clock: Callable[[], datetime] = _now
    output_dir: Path | None = None
    dry_run: bool = True

    def submit(
        self,
        script: Path,
        extra_env: Mapping[str, str] | None = None,
        *,
        store_metadata: bool = True,
        submission_dir: Path | None = None,
    ) -> dict[str, object]:
        script = Path(script)
        if not script.exists():
            raise FileNotFoundError(script)
        submitted_at = self.clock().isoformat() + "Z"
        stdout_path, stderr_path = _read_submission_paths(script)
        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
        metadata: dict[str, object] = {
            "script_path": str(script),
            "submitted_at": submitted_at,
            "submit_host": socket.gethostname(),
            "stdout_path": str(stdout_path) if stdout_path else None,
            "stderr_path": str(stderr_path) if stderr_path else None,
        }
        if self.dry_run or self.runner is None:
            job_id = str(random.randint(100000, 999999))
            metadata.update(
                {
                    "job_id": job_id,
                    "status": "simulated",
                    "command": f"sbatch {script}",
                    "stdout": f"Submitted batch job {job_id}",
                    "stderr": "",
                }
            )
        else:
            result = self.runner(["sbatch", str(script)], env=env)
            job_id = _parse_job_id(result.stdout)
            metadata.update(
                {
                    "job_id": job_id,
                    "status": "submitted",
                    "command": f"sbatch {script}",
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                    "slurm_version": self._slurm_version(env),
                }
            )
        if store_metadata:
            target_dir = Path(submission_dir or self.output_dir or script.parent)
            _ensure_dir(target_dir)
            submission_path = target_dir / "submission.json"
            _json_dump({k: v for k, v in metadata.items() if v is not None}, submission_path)
            metadata["metadata_path"] = str(submission_path)
        return metadata

    def wait(
        self,
        job_id: str,
        config: Mapping[str, object],
        *,
        timeline_path: Path | None = None,
    ) -> list[dict[str, object]]:
        poll_interval = int(config.get("poll_interval_seconds", 30))
        max_pending = int(config.get("max_pending_minutes", 20))
        max_run = int(config.get("max_run_minutes", 180))
        timeout_action = str(config.get("timeout_action") or "none").lower()
        records: list[dict[str, object]] = []
        start = self.clock()
        if self.dry_run or self.runner is None:
            records.extend(
                [
                    self._timeline_entry(job_id, "SUBMITTED", source="sbatch", at=start),
                    self._timeline_entry(
                        job_id,
                        "PENDING",
                        source="squeue",
                        at=start + timedelta(seconds=poll_interval),
                        details={"reason": "Priority"},
                    ),
                    self._timeline_entry(
                        job_id,
                        "RUNNING",
                        source="squeue",
                        at=start + timedelta(seconds=poll_interval * 2),
                        details={"node_list": "sim-node001"},
                    ),
                    self._timeline_entry(
                        job_id,
                        "COMPLETED",
                        source="sacct",
                        at=start + timedelta(minutes=min(max_run, 5)),
                        details={"elapsed": "00:05:00", "max_rss": "1024M", "alloc_gres": ""},
                    ),
                ]
            )
        else:
            exit_states = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"}
            pending_deadline = start + timedelta(minutes=max_pending)
            run_deadline = start + timedelta(minutes=max_run)
            while True:
                now = self.clock()
                result = self.runner(["squeue", "-j", job_id, "--noheader", "--format=%T %M %R"])
                state_lines = result.stdout.strip().splitlines()
                if not state_lines:
                    sacct = self.runner([
                        "sacct",
                        "-j",
                        job_id,
                        "--format=State,Elapsed,MaxRSS,AllocGRES",
                        "--parsable2",
                        "--noheader",
                    ])
                    state_parts = sacct.stdout.strip().split("|")
                    state = state_parts[0] if state_parts else "COMPLETED"
                    details = {}
                    if len(state_parts) >= 4:
                        details = {
                            "elapsed": state_parts[1],
                            "max_rss": state_parts[2],
                            "alloc_gres": state_parts[3],
                        }
                    records.append(self._timeline_entry(job_id, state, source="sacct", at=now, details=details))
                    break
                state, elapsed, *rest = state_lines[0].split(maxsplit=2)
                details = {"elapsed": elapsed}
                if rest:
                    details["reason"] = rest[0]
                records.append(self._timeline_entry(job_id, state, source="squeue", at=now, details=details))
                if state in exit_states:
                    break
                if state == "PENDING" and now > pending_deadline and timeout_action == "scancel":
                    self.runner(["scancel", job_id])
                    records.append(
                        self._timeline_entry(
                            job_id,
                            "CANCELLED",
                            source="scancel",
                            at=self.clock(),
                            details={"reason": "timeout"},
                        )
                    )
                    break
                if state == "RUNNING" and now > run_deadline and timeout_action == "scancel":
                    self.runner(["scancel", job_id])
                    records.append(
                        self._timeline_entry(
                            job_id,
                            "TIMEOUT",
                            source="scancel",
                            at=self.clock(),
                            details={"reason": "runtime limit"},
                        )
                    )
                    break
                time.sleep(poll_interval)
        if timeline_path or self.output_dir:
            target = timeline_path or (self.output_dir and Path(self.output_dir) / "job.jsonl")
            if target:
                target = Path(target)
                _ensure_dir(target.parent)
                with target.open("w", encoding="utf-8") as handle:
                    for entry in records:
                        handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return records

    def collect(
        self,
        job_id: str,
        submission: Mapping[str, object],
        dest: Path,
        *,
        create_missing: bool = True,
    ) -> dict[str, object]:
        dest = Path(dest)
        _ensure_dir(dest)
        stdout_src = submission.get("stdout_path")
        stderr_src = submission.get("stderr_path")
        artifacts = []
        for label, src in (("stdout", stdout_src), ("stderr", stderr_src)):
            if not src:
                continue
            src_path = Path(src)
            target = dest / src_path.name
            if src_path.exists():
                target.write_bytes(src_path.read_bytes())
            elif create_missing:
                target.write_text("", encoding="utf-8")
            artifacts.append({"label": label, "path": str(target), "size_bytes": target.stat().st_size})
        manifest = {
            "job_id": job_id,
            "generated_at": self.clock().isoformat() + "Z",
            "artifacts": artifacts,
        }
        manifest_path = dest / "artifact_manifest.json"
        _json_dump(manifest, manifest_path)
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    def _timeline_entry(
        self,
        job_id: str,
        state: str,
        *,
        source: str,
        at: datetime,
        details: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        return {
            "timestamp": at.isoformat() + "Z",
            "job_id": job_id,
            "source": source,
            "state": state,
            "details": dict(details) if details else {},
        }

    def _slurm_version(self, env: Mapping[str, str]) -> str | None:
        if not self.runner:
            return None
        try:
            result = self.runner(["sinfo", "--version"], env=env)
        except Exception:  # pragma: no cover - best-effort metadata
            return None
        return result.stdout.strip() or None
