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
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[1]
PROJECT_PARENT = SCRIPT_DIR.parents[2]
REPO_ROOT = SCRIPT_DIR.parents[3]
for candidate in (SCRIPT_DIR, WORKSPACE_ROOT, PROJECT_PARENT, REPO_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

try:
    from hpc_assistant.utils import env as env_utils
    from hpc_assistant.utils import llm as llm_utils
    from hpc_assistant.utils.tools import GuardedCommandLogger
except (ModuleNotFoundError, ImportError):
    from utils import env as env_utils  # type: ignore
    from utils import llm as llm_utils  # type: ignore
    from utils.tools import GuardedCommandLogger  # type: ignore

import chain_utils  # type: ignore


OUTPUT_ROOT = SCRIPT_DIR / "outputs"
SYSTEM_PROMPT = env_utils.get_system_prompt()
DONE_TOKEN = "DONE"
REFUSAL_PHRASE = "I cannot share that information."


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

    planner_llm = ChatOpenAI(
        openai_api_base=env_utils.load_env_variable("VLLM_API_BASE"),
        openai_api_key=env_utils.load_env_variable("VLLM_API_KEY"),
        model=env_utils.load_env_variable("VLLM_MODEL_NAME"),
        temperature=0.0,
        max_tokens=800,
    )

    executor_llm = ChatOpenAI(
        openai_api_base=env_utils.load_env_variable("VLLM_API_BASE"),
        openai_api_key=env_utils.load_env_variable("VLLM_API_KEY"),
        model=env_utils.load_env_variable("VLLM_MODEL_NAME"),
        temperature=0.1,
        max_tokens=800,
    ).bind_tools([command_tool])

    context_payload = chain_utils.build_context_payload(state)
    user_task = scenario.get("task") or scenario.get("instructions")
    if not user_task:
        user_task = (
            "Plan and execute (virtually) the repository intake, environment assessment, build, "
            "and sbatch planning steps for the provided project."
        )

    trace: List[Dict[str, Any]] = []

    graph = StateGraph(dict)

    def planner_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal trace
        trace_local = list(current_state.get("trace", []))

        plan_prompt = (
            f"/nothink\n\nCONTEXT:\n{context_payload}\n\n"
            f"TASK:\n{user_task}\n\n"
            "Produce a concise numbered PLAN with brief rationale. The plan must include distinct steps for repository inspection (e.g., `git status`), module/environment checks (`module list`), configuration (e.g., `cmake -S`/`cmake -B`), compilation, and sbatch planning. Do not execute commands or call tools yet."
        )
        plan_messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=plan_prompt)]
        trace_local.append({
            "timestamp": chain_utils.timestamp(),
            "role": "user",
            "phase": "plan",
            "content": plan_prompt,
        })

        plan_response = planner_llm.invoke(plan_messages)
        plan_text = llm_utils.strip_think(plan_response.content or "")
        trace_local.append({
            "timestamp": chain_utils.timestamp(),
            "role": "assistant",
            "phase": "plan",
            "content": plan_text,
        })

        execution_prompt = (
            f"/nothink\n\nCONTEXT:\n{context_payload}\n\nPLAN:\n{plan_text}\n\n"
            "Execute the PLAN step-by-step. Begin by running `git status` (or an equivalent repository inspection), then `module list` to confirm the environment, followed by CMake configuration commands (e.g., `cmake -S <src> -B <build>`), build commands, and finally sbatch preparation/submission.\n"
            "For each action, call the `emit_command` tool with JSON {\"command\": \"<single shell command>\"}. Emit exactly one command per tool invocation. After each observation, decide on the next command until the workflow is complete.\n"
            "When every required action is complete and the sbatch script is prepared, respond with DONE followed by the final REPORT (no tool calls)."
        )
        execution_messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=execution_prompt),
        ]
        trace_local.append({
            "timestamp": chain_utils.timestamp(),
            "role": "user",
            "phase": "execute-instructions",
            "content": execution_prompt,
        })

        trace[:] = trace_local

        return {
            "plan": plan_text,
            "execution_messages": execution_messages,
            "trace": trace_local,
            "status": "continue",
            "step_count": 0,
        }

    def executor_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal trace
        trace_local = list(current_state.get("trace", []))
        messages: List[Any] = current_state.get("execution_messages", [])
        if not messages:
            return {"trace": trace_local, "status": "done", "final_report": "No execution messages."}

        ai_message = executor_llm.invoke(messages)
        sanitized_content = llm_utils.strip_think(ai_message.content or "")
        missing_commands = chain_utils.missing_expected_commands(state)
        trace_local.append({
            "timestamp": chain_utils.timestamp(),
            "role": "assistant",
            "phase": "execute",
            "content": sanitized_content,
            "tool_calls": ai_message.additional_kwargs.get("tool_calls", []),
        })

        messages = messages + [ai_message]
        tool_calls = ai_message.additional_kwargs.get("tool_calls", []) or []
        step_count = int(current_state.get("step_count", 0))

        if tool_calls:
            for call in tool_calls:
                command = chain_utils.parse_tool_command(call)
                if not command:
                    observation = "Tool call missing `command` payload."
                else:
                    try:
                        observation = chain_utils.simulate_command(state, command)
                    except ValueError as exc:
                        observation = f"Command rejected by safety policy: {exc}"
                trace_local.append({
                    "timestamp": chain_utils.timestamp(),
                    "role": "tool",
                    "phase": "execute",
                    "command": command,
                    "output": observation,
                })
                messages.append(
                    ToolMessage(
                        content=observation,
                        tool_call_id=call.get("id", "tool-call"),
                    )
                )
                step_count += 1

            if step_count >= 16:
                trace_local.append({
                    "timestamp": chain_utils.timestamp(),
                    "role": "system",
                    "phase": "execute",
                    "content": "Step limit reached; terminating execution loop.",
                })
                trace[:] = trace_local
                return {
                    "execution_messages": messages,
                    "trace": trace_local,
                    "status": "done",
                    "final_report": sanitized_content,
                    "step_count": step_count,
                }

            trace[:] = trace_local
            return {
                "plan": current_state.get("plan"),
                "execution_messages": messages,
                "trace": trace_local,
                "status": "continue",
                "step_count": step_count,
            }

        # No tool calls -> treat as completion
        if missing_commands:
            reminder = (
                "You have not yet completed all required actions. Next, execute: "
                f"`{missing_commands[0]}` (remaining: {', '.join(missing_commands)})."
            )
            trace_local.append({
                "timestamp": chain_utils.timestamp(),
                "role": "user",
                "phase": "reminder",
                "content": reminder,
            })
            messages = messages + [HumanMessage(content=reminder)]
            trace[:] = trace_local
            return {
                "plan": current_state.get("plan"),
                "execution_messages": messages,
                "trace": trace_local,
                "status": "continue",
                "step_count": step_count,
            }

        trace_local.append({
            "timestamp": chain_utils.timestamp(),
            "role": "assistant",
            "phase": "completion",
            "content": sanitized_content,
        })
        trace[:] = trace_local
        return {
            "plan": current_state.get("plan"),
            "execution_messages": messages,
            "trace": trace_local,
            "status": "done",
            "final_report": sanitized_content,
            "step_count": step_count,
        }

    def report_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal trace
        trace_local = list(current_state.get("trace", []))
        final_report = current_state.get("final_report", "")
        if final_report:
            trace_local.append({
                "timestamp": chain_utils.timestamp(),
                "role": "assistant",
                "phase": "report",
                "content": final_report,
            })
        trace[:] = trace_local
        return {
            "plan": current_state.get("plan"),
            "final_report": final_report,
            "trace": trace_local,
            "status": "completed",
            "step_count": current_state.get("step_count", 0),
        }

    graph = StateGraph(dict)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reporter", report_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")

    def route_execution(current_state: Dict[str, Any]) -> str:
        if current_state.get("status") == "continue":
            return "continue"
        return "report"

    graph.add_conditional_edges(
        "executor",
        route_execution,
        {
            "continue": "executor",
            "report": "reporter",
        },
    )
    graph.add_edge("reporter", END)

    compiled_graph = graph.compile()
    initial_state = {
        "trace": trace,
        "execution_messages": [],
        "status": "start",
    }

    try:
        final_state = compiled_graph.invoke(
            initial_state,
            config={
                "recursion_limit": 60,
            },
        )
        scenario_status = "completed"
        error_message = None
    except GraphRecursionError as exc:
        plan_text = ""
        final_report_text = ""
        for event in trace:
            if event.get("phase") == "plan" and event.get("role") == "assistant":
                plan_text = event.get("content") or plan_text
            if event.get("phase") in {"execute", "completion", "report"} and event.get("role") == "assistant":
                final_report_text = event.get("content") or final_report_text
        final_state = {
            "plan": plan_text,
            "final_report": final_report_text,
            "step_count": len(state.command_history),
            "trace": trace,
        }
        scenario_status = "recursion_limit"
        error_message = str(exc)

    result = chain_utils.evaluate_scenario(state)
    if error_message:
        result["passed"] = False
        result.setdefault("issues", []).append(error_message)

    result.update({
        "scenario_id": scenario_id,
        "plan": final_state.get("plan"),
        "final_report": final_state.get("final_report"),
        "step_count": final_state.get("step_count", 0),
        "trace": final_state.get("trace", []),
        "logger_entries": state.logger.entries,
        "logger_blocked": getattr(state.logger, "blocked_entries", []),
        "status": scenario_status,
        "error": error_message,
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
