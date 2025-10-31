"""Real command execution with streaming output and guard enforcement."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from hpc_assistant.utils.tools import GuardedCommandLogger


StreamCallback = Callable[[str, str], None]


@dataclass
class CommandResult:
    """Structured record of an executed (or blocked) command."""

    command: str
    cwd: str
    returncode: Optional[int]
    stdout: str
    stderr: str
    start_time: float
    end_time: float
    blocked: bool = False
    error: Optional[str] = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["duration"] = self.duration
        return payload


class CommandExecutor:
    """Execute shell commands with guard enforcement and live streaming."""

    def __init__(self, *, log_dir: Path, logger: Optional[GuardedCommandLogger] = None) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.commands_log = self.log_dir / "commands.jsonl"
        self.logger = logger or GuardedCommandLogger(self.commands_log)

    def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        stream_callback: Optional[StreamCallback] = None,
        task_id: Optional[str] = None,
    ) -> CommandResult:
        """Execute ``command`` from ``cwd`` with optional streaming callback."""
        try:
            self.logger.log(command, task_id=task_id)
        except ValueError as exc:
            result = CommandResult(
                command=command,
                cwd=str(cwd),
                returncode=None,
                stdout="",
                stderr="",
                start_time=time.time(),
                end_time=time.time(),
                blocked=True,
                error=str(exc),
            )
            self._persist(result)
            if stream_callback:
                stream_callback("stderr", f"[GUARD] {exc}\n")
            return result

        start_time = time.time()
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        process = subprocess.Popen(
            ["bash", "-lc", command],
            cwd=str(cwd),
            env=proc_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        def _pump(stream, channel: str, buffer: list[str]) -> None:
            assert stream is not None
            for line in iter(stream.readline, ""):
                buffer.append(line)
                if stream_callback:
                    stream_callback(channel, line)
            stream.close()

        stdout_thread = threading.Thread(
            target=_pump, args=(process.stdout, "stdout", stdout_chunks), daemon=True
        )
        stderr_thread = threading.Thread(
            target=_pump, args=(process.stderr, "stderr", stderr_chunks), daemon=True
        )
        stdout_thread.start()
        stderr_thread.start()

        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = process.wait()
            if stream_callback:
                stream_callback("stderr", "[ERROR] Command timed out and was terminated.\n")

        stdout_thread.join()
        stderr_thread.join()

        end_time = time.time()
        result = CommandResult(
            command=command,
            cwd=str(cwd),
            returncode=returncode,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            start_time=start_time,
            end_time=end_time,
        )
        self._persist(result)
        return result

    def _persist(self, result: CommandResult) -> None:
        with self.commands_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result.to_dict()) + "\n")
