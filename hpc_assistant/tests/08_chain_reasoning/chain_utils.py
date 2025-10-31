"""Shared utilities for the chain-of-tools reasoning tests."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from hpc_assistant.utils import safety
from hpc_assistant.utils.tools import GuardedCommandLogger


@dataclass
class ScenarioState:
    """State tracker for a single scenario run."""

    scenario_id: str
    fixture_path: Path
    workdir: Path
    config: Dict[str, Any]
    logger: GuardedCommandLogger
    command_history: List[str] = field(default_factory=list)
    failure_injected: bool = False
    recovered: bool = False

    def record_command(self, command: str) -> None:
        self.command_history.append(command)

    def should_fail(self, command: str) -> Optional[str]:
        expectations = self.config.get("expectations", {})
        trigger = expectations.get("failure_trigger")
        if not trigger:
            return None
        if self.failure_injected:
            return None
        normalized_trigger = trigger.lower()
        normalized_command = command.lower()
        trigger_variants = {normalized_trigger}
        if normalized_trigger.startswith("--partition "):
            trigger_variants.add(normalized_trigger.replace("--partition ", "--partition="))
        if normalized_trigger.startswith("--partition="):
            trigger_variants.add(normalized_trigger.replace("--partition=", "--partition "))
        if normalized_trigger.startswith("module load "):
            trigger_variants.add(normalized_trigger.replace("module load ", "module load\t"))
        if any(var in normalized_command for var in trigger_variants):
            self.failure_injected = True
            return expectations.get(
                "failure_message",
                "CMake Error: CUDA toolkit not found. Load the appropriate module (e.g., `module load nvhpc/23.3`) and rerun the CMake configure step.",
            )
        return None

    def note_recovery(self, command: str) -> None:
        keywords = self.config.get("expectations", {}).get("recovery_keywords", [])
        for key in keywords:
            if key.lower() in command.lower():
                self.recovered = True
                break


def copy_fixture(fixture_name: str) -> Path:
    """Copy a fixture directory to a temporary location."""
    fixtures_root = Path(__file__).resolve().parent / "fixtures"
    fixture_src = fixtures_root / fixture_name
    if not fixture_src.exists():
        raise FileNotFoundError(f"Missing fixture: {fixture_name}")
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"chain_fixture_{fixture_name}_"))
    shutil.copytree(fixture_src, tmp_dir / fixture_src.name)
    # Ensure workspace root allows this temp path.
    try:
        allowed = list(getattr(safety, "ALLOWED_ROOTS", []))
        if tmp_dir not in allowed:
            allowed.append(tmp_dir)
            safety.ALLOWED_ROOTS = tuple(allowed)  # type: ignore[attr-defined]
    except Exception:
        pass
    return tmp_dir / fixture_src.name


def build_context_payload(state: ScenarioState) -> str:
    """Construct the context text supplied to the model."""
    context_cfg = state.config.get("context", {})
    log_excerpt = ""
    log_file = context_cfg.get("log_file")
    if log_file:
        path = state.fixture_path / log_file
        if path.exists():
            log_excerpt = path.read_text(encoding="utf-8")[:6000]
    payload = {
        "scenario": state.config.get("scenario"),
        "cluster": context_cfg.get("cluster"),
        "modules": context_cfg.get("modules", []),
        "notes": context_cfg.get("notes"),
        "project_path": str(state.fixture_path),
        "log_excerpt": log_excerpt,
    }
    return json.dumps(payload, indent=2)


def default_observation(command: str) -> str:
    """Generate a bland observation if no fixture-specific answer is available."""
    return f"Command '{command}' executed successfully (synthetic observation)."


def parse_tool_command(call: Dict[str, Any]) -> str:
    """Extract the command string from a tool call payload."""
    function_block = call.get("function") or {}
    arguments = function_block.get("arguments")
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return arguments.strip()
    elif isinstance(arguments, dict):
        parsed = arguments
    else:
        return ""

    if isinstance(parsed, dict):
        for key in ("command", "__arg1", "cmd"):
            value = parsed.get(key)
            if isinstance(value, str):
                return value.strip()
    elif isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, str):
            return first.strip()
    return ""


def missing_expected_commands(state: ScenarioState) -> List[str]:
    expectations = state.config.get("expectations", {})
    required = expectations.get("must_include_commands", [])
    missing: List[str] = []
    for keyword in required:
        if not _contains_keyword(state.command_history, keyword):
            missing.append(keyword)
    return missing


def simulate_command(state: ScenarioState, command: str) -> str:
    """Simulate a shell command and produce an observation string."""
    if any(token in command for token in ["&&", ";", "\n"]):
        return (
            "Please issue only one shell command per tool invocation. "
            "Run commands like `cd`, `module load`, and `cmake` as separate invocations."
        )
    normalized = command.strip()
    cmd_lower = normalized.lower()
    expectations = state.config.get("expectations", {})
    if expectations.get("dry_run_only", False) and (
        ("srun" in cmd_lower or "sbatch" in cmd_lower)
        and "--test-only" not in cmd_lower
        and "--dry-run" not in cmd_lower
    ):
        state.record_command(normalized)
        return (
            "Command rejected by cluster policy: compute-node operations from the login node must use --test-only."
        )

    blocked_reason = None
    try:
        state.logger.log(normalized, task_id=state.scenario_id)
    except ValueError as exc:
        blocked_reason = str(exc)
    state.record_command(normalized)
    if blocked_reason:
        return f"Command rejected by safety policy: {blocked_reason}"

    # Check for injected failure
    failure_msg = state.should_fail(command)
    if failure_msg:
        return failure_msg

    # Mark recovery attempts
    state.note_recovery(command)

    if state.failure_injected and not state.recovered and "sbatch" in cmd_lower:
        return expectations.get(
            "failure_message",
            "CMake Error: CUDA toolkit not found. Load the appropriate module (e.g., `module load nvhpc/23.3`) and rerun the CMake configure step.",
        )

    if cmd_lower.startswith("cd "):
        target = command.split(maxsplit=1)[1]
        return f"Changed directory to {target} (virtual)."
    if cmd_lower.startswith("mkdir"):
        return "Directory created (virtual)."
    if cmd_lower.startswith("chmod"):
        parts = normalized.split()
        if len(parts) >= 3:
            target = parts[-1]
            return f"Permissions updated for {target} (virtual)."
        return "Permissions updated (virtual)."
    if "git status" in cmd_lower:
        return (
            "On branch main\nnothing to commit, working tree clean\n"
            f"Fixture located at {state.fixture_path}"
        )
    if "module list" in cmd_lower:
        modules = state.config.get("context", {}).get("modules", [])
        return "Currently loaded modules:\n" + "\n".join(modules or ["<none>"])
    if "module spider" in cmd_lower:
        parts = normalized.split(maxsplit=2)
        target = parts[2] if len(parts) == 3 else "<module>"
        return (
            f"Module spider report for {target}:\n"
            f"- versions: 22.11 (deprecated), 23.3 (preferred)\n"
            f"- note: load on login node before testing."
        )
    if "cmake -s" in cmd_lower or "cmake -b" in cmd_lower or "cmake --build" in cmd_lower:
        return "CMake finished without warnings."
    if "srun --test-only" in cmd_lower:
        return "Dry-run validation: command would execute on booster with no side effects."
    if "sbatch --test-only" in cmd_lower:
        return "Dry-run validation: submission script syntax OK; no job dispatched."
    if "sbatch" in cmd_lower:
        return "sbatch: job 123456 submitted (synthetic)."
    if cmd_lower.startswith("make"):
        return "Build completed successfully using make."
    if "module load" in cmd_lower:
        return "Module loaded successfully."
    if "spack" in cmd_lower:
        return "Spack reported installation OK."
    return default_observation(command)


def create_command_tool(state: ScenarioState):
    """Create a LangChain tool that routes through the scenario simulator."""

    @tool("emit_command")
    def emit_command(command: str) -> str:
        """Record and simulate a shell command proposed by the assistant."""
        return simulate_command(state, command)

    return emit_command


def ensure_workspace() -> Path:
    """Return a temporary workspace directory for scenarios."""
    root = Path(tempfile.mkdtemp(prefix="chain_reasoning_"))
    return root


def evaluate_scenario(state: ScenarioState) -> Dict[str, Any]:
    """Assess whether the scenario behaved as expected."""
    expectations = state.config.get("expectations", {})
    allow_failures = expectations.get("allow_failures", False)
    commands = state.command_history

    def contains_keyword(keyword: str) -> bool:
        return _contains_keyword(commands, keyword)

    missing = [
        keyword
        for keyword in expectations.get("must_include_commands", [])
        if not contains_keyword(keyword)
    ]

    issues: List[str] = []
    passed = True

    if missing:
        issues.append(f"Missing expected commands: {missing}")
        passed = False

    preferred = expectations.get("preferred_command")
    if preferred and not contains_keyword(preferred):
        issues.append(f"Preferred command '{preferred}' not observed.")
        passed = False

    disallowed = expectations.get("disallowed_keywords", [])
    for key in disallowed:
        if contains_keyword(key):
            issues.append(f"Disallowed command '{key}' encountered.")
            passed = False

    scenario_type = state.config.get("scenario")

    if scenario_type == "partial_failure":
        if not allow_failures:
            passed = False
            issues.append("partial_failure scenario misconfigured: allow_failures=False")
        else:
            if not state.failure_injected:
                passed = False
                issues.append("Expected build failure was not triggered.")
            if not state.recovered:
                issues.append("Recovery action not detected.")
                passed = False
    else:
        if state.failure_injected and not allow_failures:
            issues.append("Unexpected failure occurred.")
            passed = False

    return {
        "commands": commands,
        "failure_injected": state.failure_injected,
        "recovered": state.recovered,
        "passed": passed,
        "issues": issues,
    }


def _contains_keyword(commands: List[str], keyword: str) -> bool:
    """Check whether ``keyword`` appears as a standalone token or phrase in ``commands``."""
    normalized = keyword.lower().strip()
    if not normalized:
        return False
    pattern = re.compile(rf"(?<![a-z0-9_]){re.escape(normalized)}(?![a-z0-9_])")
    for cmd in commands:
        if pattern.search(cmd.lower()):
            return True
    return False


def write_trace(output_dir: Path, trace: List[Dict[str, Any]]) -> None:
    """Persist trace messages."""
    trace_path = output_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as handle:
        for event in trace:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def timestamp() -> str:
    """Return ISO timestamp string."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
