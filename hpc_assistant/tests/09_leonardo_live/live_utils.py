"""Shared utilities for the Leonardo live command harness."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from hpc_assistant.utils.tools import GuardedCommandLogger

try:  # pragma: no cover - fallback for script execution
    from .command_executor import CommandExecutor, CommandResult
except ImportError:
    from command_executor import CommandExecutor, CommandResult  # type: ignore


@dataclass
class ScenarioState:
    """Runtime state for a live Leonardo scenario."""

    scenario_id: str
    workdir: Path
    current_dir: Path
    output_dir: Path
    config: Dict[str, Any]
    logger: GuardedCommandLogger
    executor: CommandExecutor
    command_results: List[CommandResult] = field(default_factory=list)
    status_updates: List[Dict[str, str]] = field(default_factory=list)

    def record_result(self, result: CommandResult) -> None:
        self.command_results.append(result)

    def add_status(self, message: str, *, phase: str) -> None:
        entry = {
            "timestamp": timestamp(),
            "phase": phase,
            "message": message,
        }
        self.status_updates.append(entry)
        status_path = self.output_dir / "status.log"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        with status_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def change_directory(self, target: Path) -> None:
        self.current_dir = target


def ensure_workspace(prefix: str = "leonardo_live_") -> Path:
    """Create a temporary workspace for a scenario."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def prepare_output_dir(root: Path, scenario_id: str) -> Path:
    output_dir = root / scenario_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def timestamp() -> str:
    """Return ISO timestamp string."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_fixture_documents(doc_root: Path) -> List[Dict[str, str]]:
    """Load markdown documents bundled with the fixture."""
    documents: List[Dict[str, str]] = []
    for path in sorted(doc_root.glob("*.md")):
        documents.append(
            {
                "name": path.name,
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return documents


def build_context_payload(
    *,
    scenario: Dict[str, Any],
    documents: List[Dict[str, str]],
    live_notes: Optional[str] = None,
) -> str:
    """Assemble the context JSON passed to the planner/executor."""
    payload = {
        "scenario": scenario.get("scenario"),
        "task": scenario.get("task"),
        "cluster": scenario.get("context", {}).get("cluster"),
        "modules": scenario.get("context", {}).get("modules", []),
        "notes": scenario.get("context", {}).get("notes"),
        "documents": [
            {"name": doc["name"], "excerpt": doc["content"][:4000]}
            for doc in documents
        ],
        "live_notes": live_notes,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def collect_live_notes(paths: List[Path]) -> str:
    """Read small files from the workspace to supply as additional context."""
    notes: List[str] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        notes.append(f"# {path.name}\n{content[:4000]}")
    return "\n\n".join(notes)


def evaluate_scenario(state: ScenarioState) -> Dict[str, Any]:
    """Assess whether the scenario satisfied the required behaviours."""
    expectations = state.config.get("expectations", {})
    required = expectations.get("must_include_commands", [])
    preferred = expectations.get("preferred_command")
    disallowed = expectations.get("disallowed_keywords", [])

    commands = [result.command for result in state.command_results if not result.blocked]
    missing = [cmd for cmd in required if cmd and not _contains_keyword(commands, cmd)]

    issues: List[str] = []
    passed = True

    if missing:
        issues.append(f"Missing expected commands: {missing}")
        passed = False

    if preferred and not _contains_keyword(commands, preferred):
        issues.append(f"Preferred command '{preferred}' not observed.")
        passed = False

    for keyword in disallowed:
        if _contains_keyword(commands, keyword):
            issues.append(f"Disallowed command '{keyword}' encountered.")
            passed = False

    allow_failures = expectations.get("allow_failures", False)
    if not allow_failures:
        failures = [r for r in state.command_results if r.returncode not in (0, None)]
        if failures:
            issues.append(f"{len(failures)} command(s) failed unexpectedly.")
            passed = False

    return {
        "passed": passed,
        "issues": issues,
        "commands": commands,
        "status_updates": state.status_updates,
    }


def cleanup_workspace(path: Path) -> None:
    """Remove a temporary workspace directory."""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def expected_command_gaps(state: ScenarioState) -> List[str]:
    """Return commands that have not yet been observed."""
    expectations = state.config.get("expectations", {})
    required = expectations.get("must_include_commands", [])
    commands = [result.command for result in state.command_results if not result.blocked]
    return [cmd for cmd in required if cmd and not _contains_keyword(commands, cmd)]


def bootstrap_workspace(state: ScenarioState) -> None:
    """Populate the workspace with helper files for specific scenarios."""
    if state.scenario_id == "tinygrad-setup":
        scripts_dir = state.workdir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_path = scripts_dir / "run_tinygrad.sbatch"
        if not script_path.exists():
            script_path.write_text(
                "#!/bin/bash\n#SBATCH --job-name=tinygrad-dryrun\n#SBATCH --partition=booster\n#SBATCH --gpus-per-node=1\n#SBATCH --time=00:05:00\n\n"
                "echo \"Dry-run: tinygrad inference\"\npython3 -c 'print(\"tinygrad dry-run\")'\n",
                encoding="utf-8",
            )
    elif state.scenario_id == "unsloth-finetune":
        datasets_dir = state.workdir / "datasets"
        datasets_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir = state.workdir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_path = scripts_dir / "finetune_booster.sbatch"
        if not script_path.exists():
            script_path.write_text(
                "#!/bin/bash\n#SBATCH --job-name=unsloth-dryrun\n#SBATCH --partition=booster\n#SBATCH --gpus-per-node=1\n#SBATCH --time=00:10:00\n\n"
                "echo \"Dry-run: unsloth finetune\"\npython3 -c 'print(\"unsloth dry-run\")'\n",
                encoding="utf-8",
            )


def _contains_keyword(commands: List[str], keyword: str) -> bool:
    normalized = keyword.lower().strip()
    if not normalized:
        return False
    for cmd in commands:
        if normalized in cmd.lower():
            return True
    return False
