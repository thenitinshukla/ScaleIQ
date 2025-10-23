"""Static command safety policy for the HPC assistant."""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAFE_WORKSPACE = PROJECT_ROOT

# Files and directories critical to the guard/system which must never be touched.
PROTECTED_PATHS = [
    PROJECT_ROOT / "utils",
    PROJECT_ROOT / "requirements.txt",
]

# Denylisted command heads (case-insensitive).
DENY_COMMANDS = {
    "rm",
    "rmdir",
    "mv",
    "chmod",
    "chown",
    "chgrp",
    "dd",
    "mkfs",
    "mount",
    "umount",
    "fdisk",
    "wipefs",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
    "kill",
    "pkill",
    "killall",
    "curl",
    "wget",
    "scp",
    "rsync",
    "nc",
    "netcat",
    "socat",
    "python",
    "python3",
    "perl",
    "ruby",
    "php",
    "node",
    "bash",
    "sh",
    "zsh",
    "fish",
    "eval",
    "exec",
    "sudo",
    "su",
    "truncate",
    "tee",
    "dd",
}

# Allowed commands without additional checks (subset).
ALLOWED_COMMANDS = {
    "ls",
    "pwd",
    "whoami",
    "module",
    "echo",
    "cat",
    "head",
    "tail",
    "grep",
    "sed",
    "awk",
    "touch",
    "mkdir",
    "cp",
    "stat",
    "sbatch",
    "squeue",
    "sacct",
    "sinfo",
    "env",
    "printf",
    "sleep",
}

# Patterns indicating dangerous behaviour (regex applied case-insensitively).
DENY_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/", re.IGNORECASE),
    re.compile(r"rm\s+.*--no-preserve-root", re.IGNORECASE),
    re.compile(r":\(\)\s*{\s*:\s*\|\s*:\s*;\s*}\s*;\s*:", re.IGNORECASE),  # fork bomb
    re.compile(r"mkfs\.", re.IGNORECASE),
    re.compile(r"dd\s+if=", re.IGNORECASE),
    re.compile(r"shutdown\b", re.IGNORECASE),
    re.compile(r"reboot\b", re.IGNORECASE),
    re.compile(r"poweroff\b", re.IGNORECASE),
    re.compile(r"halt\b", re.IGNORECASE),
    re.compile(r"kill\s+-9\s+1\b", re.IGNORECASE),
    re.compile(r"git\s+reset\s+--hard", re.IGNORECASE),
    re.compile(r"git\s+clean\s+-dfx", re.IGNORECASE),
    re.compile(r"curl\s+.*\|\s*(bash|sh)", re.IGNORECASE),
    re.compile(r"wget\s+.*\|\s*(bash|sh)", re.IGNORECASE),
    re.compile(r"\bchattr\b", re.IGNORECASE),
    re.compile(r"systemctl\b", re.IGNORECASE),
    re.compile(r"dconf\b", re.IGNORECASE),
]

# Paths outside the workspace root are forbidden.
ALLOWED_ROOTS: Sequence[Path] = [SAFE_WORKSPACE]

# Additional file extensions that should never be overwritten.
PROTECTED_EXTENSIONS = {".so", ".dylib", ".dll", ".bin"}

REDIRECTION_OPERATORS = {
    ">",
    ">>",
    "1>",
    "2>",
    "&>",
    "|>",
    "<",
    "<<",
    "<<<",
}


@dataclass
class ValidationResult:
    command: str
    is_allowed: bool
    reason: Optional[str] = None
    matched_rule: Optional[str] = None


def _normalize_segments(command: str) -> List[str]:
    """Split the command into segments separated by operators (;, &&, ||, |)."""
    segments: List[str] = []
    current = []
    tokens = shlex.split(command, posix=True)
    special = {";", "&&", "||", "|", "||", "&&"}
    for token in tokens:
        if token in special:
            if current:
                segments.append(" ".join(current))
                current = []
        else:
            current.append(token)
    if current:
        segments.append(" ".join(current))
    if not segments:
        segments.append(command.strip())
    return segments


def _check_patterns(command: str) -> Optional[str]:
    for pattern in DENY_PATTERNS:
        if pattern.search(command):
            return f"Pattern {pattern.pattern} matched"
    return None


def _split_tokens(segment: str) -> List[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.strip().split()


def _resolve_path(path: str) -> Optional[Path]:
    try:
        expanded = os.path.expanduser(os.path.expandvars(path))
        resolved = Path(expanded).resolve()
        return resolved
    except (OSError, RuntimeError):
        return None


def _is_path_protected(path: Path) -> bool:
    for protected in PROTECTED_PATHS:
        try:
            if path == protected or protected in path.parents:
                return True
        except RuntimeError:
            continue
    return False


def _within_allowed_roots(path: Path) -> bool:
    for root in ALLOWED_ROOTS:
        try:
            if root == path or root in path.parents:
                return True
        except RuntimeError:
            continue
    return False


def _contains_protected_extension(path: Path) -> bool:
    return path.suffix.lower() in PROTECTED_EXTENSIONS


def _strip_redirection_prefix(token: str) -> Tuple[bool, Optional[str]]:
    for op in sorted(REDIRECTION_OPERATORS, key=len, reverse=True):
        if token.startswith(op) and token != op:
            remainder = token[len(op) :].strip()
            if remainder:
                return True, remainder
    return False, None


def _path_arguments(tokens: List[str]) -> Iterable[str]:
    i = 0
    length = len(tokens)
    while i < length:
        token = tokens[i]
        if not token:
            i += 1
            continue
        if token in REDIRECTION_OPERATORS:
            if i + 1 < length:
                yield tokens[i + 1]
            i += 2
            continue
        stripped, remainder = _strip_redirection_prefix(token)
        if stripped and remainder:
            yield remainder
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        if "=" in token and token.startswith("--"):
            _, value = token.split("=", 1)
            yield value
            i += 1
            continue
        yield token
        i += 1


def _validate_segment(segment: str) -> ValidationResult:
    segment = segment.strip()
    if not segment:
        return ValidationResult(segment, False, reason="Empty command segment")

    pattern_reason = _check_patterns(segment)
    if pattern_reason:
        return ValidationResult(segment, False, reason=pattern_reason, matched_rule="pattern")

    tokens = _split_tokens(segment)
    if not tokens:
        return ValidationResult(segment, False, reason="Unable to parse command tokens")

    head = tokens[0].lower()
    head_allowed = head in ALLOWED_COMMANDS

    if head in DENY_COMMANDS:
        return ValidationResult(segment, False, reason=f"Command '{head}' is denylisted", matched_rule="deny_command")

    # Inspect paths and arguments.
    for arg in _path_arguments(tokens[1:]):
        if arg.startswith("-"):
            continue
        resolved = _resolve_path(arg)
        if resolved is None:
            continue
        if _is_path_protected(resolved):
            return ValidationResult(segment, False, reason=f"Path '{resolved}' is protected", matched_rule="protected_path")
        if not _within_allowed_roots(resolved):
            return ValidationResult(segment, False, reason=f"Path '{resolved}' is outside allowed roots", matched_rule="outside_root")
        if _contains_protected_extension(resolved):
            return ValidationResult(segment, False, reason=f"File extension '{resolved.suffix}' is protected", matched_rule="protected_extension")

    # Detect subshells or function calls executing native code.
    if any(x in segment for x in ("$(", "`", ";", "&&", "||", "|", "{", "}")):
        if not head_allowed:
            return ValidationResult(segment, False, reason="Composite command with operators is not permitted", matched_rule="composite")
        # even for allowed commands, reject if composite operator present to stay conservative
        return ValidationResult(segment, False, reason="Composite command with operators is not permitted", matched_rule="composite")

    if head_allowed:
        return ValidationResult(segment, True)

    # Fallback: deny by default (explicit allowlist only).
    return ValidationResult(segment, False, reason=f"Command '{head}' is not explicitly allowed", matched_rule="default_deny")


def validate_command(command: str) -> ValidationResult:
    command = command.strip()
    if not command:
        return ValidationResult(command, False, reason="Command is empty")

    segments = _normalize_segments(command)
    reasons: List[Tuple[str, str]] = []
    for segment in segments:
        result = _validate_segment(segment)
        if not result.is_allowed:
            reasons.append((segment, result.reason or "Rejected"))

    if reasons:
        first_segment, reason = reasons[0]
        return ValidationResult(
            command,
            False,
            reason=f"Segment '{first_segment}' blocked: {reason}",
            matched_rule=";".join(filter(None, (result.matched_rule for result in [_validate_segment(segment) for segment in segments]))),
        )

    return ValidationResult(command, True)
