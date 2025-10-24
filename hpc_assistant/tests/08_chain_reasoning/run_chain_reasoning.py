#!/usr/bin/env python3
"""Run reasoning-chain scenarios that exercise multi-step tool usage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

# Ensure both local utils and package imports are available
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[1]
PROJECT_PARENT = SCRIPT_DIR.parents[2]
REPO_ROOT = SCRIPT_DIR.parents[3]
for candidate in (WORKSPACE_ROOT, PROJECT_PARENT, REPO_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

try:
    from hpc_assistant.utils import env as env_utils
    from hpc_assistant.utils import llm as llm_utils
    from hpc_assistant.utils.tools import GuardedCommandLogger
    from . import chain_utils
except ModuleNotFoundError:
    from utils import env as env_utils  # type: ignore
    from utils import llm as llm_utils  # type: ignore
    from utils.tools import GuardedCommandLogger  # type: ignore
    from tests.chain_reasoning import chain_utils  # type: ignore


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "outputs"
SYSTEM_PROMPT = env_utils.get_system_prompt()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run chain-of-tools reasoning harness.")
    parser.add_argument(
        "--requests-path",
        type=Path,
        default=SCRIPT_DIR / "requests.json",
        help="Path to scenarios configuration JSON.",
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Optional limit on number of scenarios to execute.",
    )
    return parser.parse_args()


def load_scenarios(path: Path, limit: int | None = None) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing scenario file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Scenario file must contain a list of objects")
    if limit is not None:
        data = data[:limit]
    return data


def build_messages(context_payload: str, user_task: str) -> List[SystemMessage | HumanMessage]:
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    combined_task = (
        f"/nothink\n\nCONTEXT:\n{context_payload}\n\n"
        f"TASK:\n{user_task}\n"
    )
    messages.append(HumanMessage(content=combined_task))
    return messages


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    scenario_id = scenario.get("id", "unknown")
    fixture_name = scenario.get("fixture")
    if not fixture_name:
        raise ValueError(f"Scenario {scenario_id} missing fixture")

    fixture_path = chain_utils.copy_fixture(fixture_name)
    workdir = chain_utils.ensure_workspace()

    logger = GuardedCommandLogger()
    state = chain_utils.ScenarioState(
        scenario_id=scenario_id,
        fixture_path=fixture_path,
        workdir=workdir,
        config=scenario,
        logger=logger,
    )

    command_tool = chain_utils.create_command_tool(state)

    llm = ChatOpenAI(
        openai_api_base=env_utils.load_env_variable("VLLM_API_BASE"),
        openai_api_key=env_utils.load_env_variable("VLLM_API_KEY"),
        model=env_utils.load_env_variable("VLLM_MODEL_NAME"),
        temperature=0.1,
        max_tokens=1200,
    ).bind_tools([command_tool])

    trace: List[Dict[str, Any]] = []

    context_payload = chain_utils.build_context_payload(state)
    user_task = scenario.get("task") or scenario.get("instructions")
    if not user_task:
        user_task = (
            "Plan and execute (virtually) the repository intake, environment assessment, build, "
            "and sbatch planning steps for the provided project."
        )
    messages = build_messages(context_payload, user_task)
    trace.append({
        "timestamp": chain_utils.timestamp(),
        "role": "user",
        "content": messages[-1].content,
    })

    # First turn: expect plan + potential command/tool call
    ai_message = llm.invoke(messages)
    trace.append({
        "timestamp": chain_utils.timestamp(),
        "role": "assistant",
        "content": ai_message.content,
        "tool_calls": ai_message.additional_kwargs.get("tool_calls", []),
    })

    # Process any tool calls until model produces final report
    messages.append(ai_message)
    tool_calls = ai_message.additional_kwargs.get("tool_calls", []) or []

    iteration = 0
    max_iterations = 6
    while tool_calls and iteration < max_iterations:
        iteration += 1
        observations = []
        for call in tool_calls:
            if call.get("name") != "emit_command":
                observations.append((call, "Tool not supported."))
                continue
            command = call.get("args", {}).get("command") or call.get("args", {}).get("__arg1", "")
            if not command:
                observations.append((call, "No command provided."))
                continue
            output = chain_utils.simulate_command(state, command)
            observations.append((call, output))

        for call, output in observations:
            trace.append({
                "timestamp": chain_utils.timestamp(),
                "role": "tool",
                "tool": call.get("name"),
                "command": call.get("args"),
                "output": output,
            })
            messages.append(
                ToolMessage(
                    content=output,
                    tool_call_id=call.get("id", "tool-call"),
                )
            )

        ai_message = llm.invoke(messages)
        trace.append({
            "timestamp": chain_utils.timestamp(),
            "role": "assistant",
            "content": ai_message.content,
            "tool_calls": ai_message.additional_kwargs.get("tool_calls", []),
        })
        messages.append(ai_message)
        tool_calls = ai_message.additional_kwargs.get("tool_calls", []) or []

    result = chain_utils.evaluate_scenario(state)
    result.update({
        "scenario_id": scenario_id,
        "trace": trace,
        "logger_entries": state.logger.entries,
        "logger_blocked": getattr(state.logger, "blocked_entries", []),
    })
    return result


def main() -> int:
    args = parse_args()

    scenarios = load_scenarios(args.requests_path, args.max_prompts)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_summary: List[Dict[str, Any]] = []

    for scenario in scenarios:
        scenario_id = scenario.get("id", "unknown")
        print(f"[INFO] Running scenario {scenario_id}")
        result = run_scenario(scenario)
        scenario_dir = OUTPUT_ROOT / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)

        chain_utils.write_trace(scenario_dir, result.pop("trace"))

        with (scenario_dir / "result.json").open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)

        status = "PASS" if result.get("passed") else "FAIL"
        issues = result.get("issues", [])
        if issues:
            print(f"[{status}] {scenario_id} – {issues}")
        else:
            print(f"[{status}] {scenario_id}")
        run_summary.append({"id": scenario_id, "passed": result.get("passed"), "issues": issues})

    summary_path = OUTPUT_ROOT / "summary.json"
    summary_payload = {
        "scenarios": run_summary,
        "total": len(run_summary),
        "passed": sum(1 for item in run_summary if item["passed"]),
        "failed": sum(1 for item in run_summary if not item["passed"]),
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Results stored under {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
