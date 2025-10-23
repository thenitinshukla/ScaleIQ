"""Reusable LangChain tool definitions and logging helpers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import Tool

from . import safety


class CommandLogger:
    """Append-only logger for proposed shell commands."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._log_path = log_path
        self._entries: List[Dict[str, Any]] = []
        if self._log_path is not None:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def entries(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def log(self, command: str, *, task_id: Optional[str] = None) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat() + "Z"
        entry: Dict[str, Any] = {"timestamp": timestamp, "command": command}
        if task_id:
            entry["task_id"] = task_id
        self._entries.append(entry)
        if self._log_path is not None:
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        return entry

    def clear(self) -> None:
        self._entries.clear()


class GuardedCommandLogger(CommandLogger):
    """Append-only logger that enforces the safety policy before logging."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        super().__init__(log_path)
        self._blocked: List[Dict[str, Any]] = []

    def log(self, command: str, *, task_id: Optional[str] = None) -> Dict[str, Any]:
        validation = safety.validate_command(command)
        if not validation.is_allowed:
            blocked_entry: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "command": command,
                "reason": validation.reason or "Command blocked by safety policy",
                "matched_rule": validation.matched_rule,
                "status": "blocked",
            }
            if task_id:
                blocked_entry["task_id"] = task_id
            self._blocked.append(blocked_entry)
            if self._log_path is not None:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with self._log_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(blocked_entry) + "\n")
            raise ValueError(blocked_entry["reason"])
        entry = super().log(command, task_id=task_id)
        entry["status"] = "accepted"
        return entry

    @property
    def blocked_entries(self) -> List[Dict[str, Any]]:
        return list(self._blocked)

    def clear(self) -> None:
        super().clear()
        self._blocked.clear()


def build_emit_command_tool(logger: CommandLogger) -> Tool:
    """Return a LangChain tool that records proposed shell commands."""

    def _emit_command(command: Optional[str] = None, **kwargs: Any) -> str:
        candidate = command or kwargs.get("command") or kwargs.get("__arg1")
        if not candidate:
            raise ValueError("emit_command requires a 'command' argument")
        task_id = kwargs.get("task_id")
        try:
            logger.log(candidate, task_id=task_id)
            return "Command logged"
        except ValueError as exc:
            return f"Command rejected: {exc}"

    return Tool(
        name="emit_command",
        description="Record a shell command proposed by the assistant. Do not execute it.",
        func=_emit_command,
    )
