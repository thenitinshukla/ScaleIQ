#!/usr/bin/env python3
"""Execute live Leonardo scenarios with real command feedback."""

from __future__ import annotations

import argparse
import json
import sys
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, StateGraph

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
except ModuleNotFoundError:
    from utils import env as env_utils  # type: ignore
    from utils import llm as llm_utils  # type: ignore

import live_utils  # type: ignore
from command_executor import CommandExecutor, CommandResult  # type: ignore
from hpc_assistant.utils.tools import GuardedCommandLogger

DOC_ROOT = SCRIPT_DIR / "fixtures" / "documents"
OUTPUT_ROOT = SCRIPT_DIR / "outputs"
DONE_TOKEN = "DONE"
REFUSAL_PHRASE = "I cannot share that information."
STATUS_PREFIX = "STATUS:"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Leonardo live command scenarios.")
    parser.add_argument(
        "--requests-path",
        type=Path,
        default=SCRIPT_DIR / "requests.json",
        help="Path to the JSON scenario definitions.",
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Limit the number of scenarios to execute.",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Retain temporary workspaces for inspection.",
    )
    return parser.parse_args()


def load_scenarios(path: Path, limit: Optional[int]) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing scenario file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Scenario file must contain a list of objects.")
    if limit is not None:
        data = data[:limit]
    return data


def load_documents() -> List[Dict[str, str]]:
    return live_utils.load_fixture_documents(DOC_ROOT)


def extract_status_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith(STATUS_PREFIX):
            return stripped[len(STATUS_PREFIX) :].strip()
    return None


def parse_tool_command(call: Dict[str, Any]) -> str:
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


def parse_tool_query(call: Dict[str, Any]) -> str:
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
        for key in ("query", "question", "prompt", "__arg1"):
            value = parsed.get(key)
            if isinstance(value, str):
                return value.strip()
    elif isinstance(parsed, list) and parsed:
        first = parsed[0]
        if isinstance(first, str):
            return first.strip()
    return ""


def format_command_result(result: CommandResult) -> str:
    if result.blocked:
        return f"Command rejected by safety policy: {result.error or 'Command blocked.'}"
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    stdout_snippet = stdout[:1200] if stdout else "<no stdout>"
    stderr_snippet = stderr[:800] if stderr else "<no stderr>"
    return (
        f"Command: {result.command}\n"
        f"Exit code: {result.returncode}\n"
        f"CWD: {result.cwd}\n"
        f"Stdout:\n{stdout_snippet}\n"
        f"Stderr:\n{stderr_snippet}"
    )


def run_scenario(
    scenario: Dict[str, Any],
    *,
    documents: List[Dict[str, str]],
    planner_llm: ChatOpenAI,
    executor_llm: ChatOpenAI,
    keep_workspace: bool,
) -> Dict[str, Any]:
    scenario_id = scenario.get("id", "unknown")
    print(f"[INFO] Running scenario {scenario_id}", flush=True)

    timestamp_suffix = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    scenario_output_root = OUTPUT_ROOT / timestamp_suffix
    scenario_output_root.mkdir(parents=True, exist_ok=True)
    output_dir = live_utils.prepare_output_dir(scenario_output_root, scenario_id)

    workspace = live_utils.ensure_workspace()
    logger = GuardedCommandLogger(output_dir / "guard_log.jsonl")
    executor = CommandExecutor(log_dir=output_dir, logger=logger)
    state = live_utils.ScenarioState(
        scenario_id=scenario_id,
        workdir=workspace,
        current_dir=workspace,
        output_dir=output_dir,
        config=scenario,
        logger=logger,
        executor=executor,
    )

    live_utils.bootstrap_workspace(state)

    stream_lock = threading.Lock()
    stream_path = output_dir / "command_stream.log"

    def stream_callback(channel: str, text: str) -> None:
        with stream_lock:
            with stream_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "timestamp": live_utils.timestamp(),
                            "channel": channel,
                            "text": text,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            prefix = f"[{scenario_id}][{channel.upper()}]"
            print(f"{prefix} {text}", end="", flush=True)

    @tool("emit_command")
    def emit_command(command: str) -> str:
        """Submit a shell command for guarded execution on Leonardo."""
        return f"Command received: {command}"

    environment_hints = live_utils.gather_environment_hints()

    context_payload = live_utils.build_context_payload(
        scenario=scenario,
        documents=documents,
        live_notes=None,
        environment_hints=environment_hints,
    )

    context_index: List[Dict[str, str]] = []
    for doc in documents:
        context_index.append({"source": doc["name"], "content": doc["content"]})
    if environment_hints:
        context_index.append({"source": "environment_hints", "content": environment_hints})
    scenario_notes = scenario.get("context", {}).get("notes")
    if scenario_notes:
        context_index.append({"source": "scenario_notes", "content": scenario_notes})

    @tool("fetch_context")
    def fetch_context(query: str) -> str:
        """Retrieve relevant guidance from the Leonardo knowledge base."""
        normalized = (query or "").strip().lower()
        if not normalized:
            return "Provide a query describing what you need to know."
        matches: List[Dict[str, str]] = []
        for entry in context_index:
            text_lower = entry["content"].lower()
            if normalized in text_lower:
                idx = text_lower.index(normalized)
                start = max(0, idx - 200)
                end = min(len(entry["content"]), idx + 200)
                snippet = entry["content"][start:end]
                matches.append({"source": entry["source"], "excerpt": snippet})
        if not matches:
            # fallback: return first 3 docs
            fallback = context_index[:3]
            return json.dumps({"matches": fallback}, ensure_ascii=False, indent=2)
        return json.dumps({"matches": matches[:3]}, ensure_ascii=False, indent=2)

    bound_executor_llm = executor_llm.bind_tools([emit_command, fetch_context])

    system_prompt = env_utils.get_system_prompt()
    trace: List[Dict[str, Any]] = []

    graph = StateGraph(dict)

    def planner_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        trace_local = list(current_state.get("trace", []))
        plan_prompt = (
            f"CONTEXT:\n{context_payload}\n\n"
            f"TASK:\n{scenario.get('task')}\n\n"
            "Draft a concise numbered PLAN that begins with environment reconnaissance (e.g., `pwd`, `ls`, reviewing README, checking available modules with `module avail`, listing existing Conda/uv environments)."
            " Indicate when you will consult `fetch_context` for cluster policies. Only after the reconnaissance describe repository cloning, dependency setup, validation commands, and sbatch dry-run preparation."
            " Include relevant safety reminders for the Leonardo login node."
        )
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=plan_prompt)]
        plan_response = planner_llm.invoke(messages)
        raw_plan = plan_response.content or ""
        for thought in re.findall(r"<think>(.*?)</think>", raw_plan, flags=re.DOTALL | re.IGNORECASE):
            print(f"[{scenario_id}][THINK]\n{thought.strip()}\n", flush=True)
        plan_text = llm_utils.strip_think(raw_plan)
        print(f"[{scenario_id}] PLAN\n{plan_text}\n", flush=True)

        trace_local.append(
            {
                "timestamp": live_utils.timestamp(),
                "role": "user",
                "phase": "plan",
                "content": plan_prompt,
            }
        )
        trace_local.append(
            {
                "timestamp": live_utils.timestamp(),
                "role": "assistant",
                "phase": "plan",
                "content": plan_text,
            }
        )

        execution_prompt = (
            f"CONTEXT:\n{context_payload}\n\nPLAN:\n{plan_text}\n\n"
            "Execute the PLAN step-by-step. Begin with reconnaissance: inspect the working directory (`pwd`, `ls`, `ls scripts`), review repository files once cloned, check module availability (`module avail nvhpc`), and list existing environments (`conda env list`, `uv toolchain list`)."
            " Before mutating the environment, issue at least one `fetch_context` query to recall relevant Leonardo policies or tooling tips, then continue to use it whenever new questions arise."
            " After gathering the requisite information, carry out cloning, dependency installation (consider `python3 -m pip` or activating existing environments), validation tests, and finally generate an sbatch dry-run."
            " After each observation, emit a one-line status beginning with 'STATUS:' summarising the result and next intention."
            " For every shell action, call the `emit_command` tool with JSON {\"command\": \"<single shell command>\"}; never bundle multiple commands."
            " Only respond with DONE once all required reconnaissance, installations, validations, and sbatch dry-run commands have completed successfully."
        )

        trace_local.append(
            {
                "timestamp": live_utils.timestamp(),
                "role": "user",
                "phase": "execute-instructions",
                "content": execution_prompt,
            }
        )

        trace[:] = trace_local
        return {
            "plan": plan_text,
            "messages": [SystemMessage(content=system_prompt), HumanMessage(content=execution_prompt)],
            "trace": trace_local,
            "status": "continue",
        }

    def executor_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        trace_local = list(current_state.get("trace", []))
        messages: List[Any] = current_state.get("messages", [])
        if not messages:
            return {"trace": trace_local, "status": "done", "final_report": "No execution messages."}

        ai_message = bound_executor_llm.invoke(messages)
        raw_content = ai_message.content or ""
        for thought in re.findall(r"<think>(.*?)</think>", raw_content, flags=re.DOTALL | re.IGNORECASE):
            print(f"[{scenario_id}][THINK]\n{thought.strip()}\n", flush=True)
        sanitized_content = llm_utils.strip_think(raw_content)
        status_line = extract_status_line(sanitized_content)
        if status_line:
            state.add_status(status_line, phase="assistant")

        trace_local.append(
            {
                "timestamp": live_utils.timestamp(),
                "role": "assistant",
                "phase": "execute",
                "content": sanitized_content,
                "tool_calls": ai_message.additional_kwargs.get("tool_calls", []),
            }
        )
        print(f"[{scenario_id}][ASSISTANT]\n{sanitized_content}\n", flush=True)

        tool_calls = ai_message.additional_kwargs.get("tool_calls", []) or []
        messages = messages + [ai_message]

        if tool_calls:
            for call in tool_calls:
                function_meta = call.get("function") or {}
                tool_name = function_meta.get("name")
                if tool_name == "fetch_context":
                    query = parse_tool_query(call)
                    observation = fetch_context(query)
                    command_label = f"fetch_context:{query}"
                    state.record_tool_usage(command_label)
                else:
                    command = parse_tool_command(call)
                    command_label = command or "<empty>"
                    if not command:
                        observation = "Tool call missing `command` payload."
                    elif command.lower().startswith("cd "):
                        observation = handle_directory_change(state, command, stream_callback)
                    else:
                        result = state.executor.run(
                            command,
                            cwd=state.current_dir,
                            stream_callback=stream_callback,
                            task_id=scenario_id,
                        )
                        state.record_result(result)
                        observation = format_command_result(result)
                        if result.returncode not in (0, None):
                            failure_prompt = (
                                "STATUS: A command failed. Investigate by inspecting directories, checking module and environment"
                                " availability, or querying fetch_context before retrying."
                            )
                            state.add_status(failure_prompt, phase="reminder")
                            trace_local.append(
                                {
                                    "timestamp": live_utils.timestamp(),
                                    "role": "user",
                                    "phase": "reminder",
                                    "content": failure_prompt,
                                }
                            )
                            messages.append(HumanMessage(content=failure_prompt))

                trace_local.append(
                    {
                        "timestamp": live_utils.timestamp(),
                        "role": "tool",
                        "phase": "execute",
                        "command": command_label,
                        "output": observation,
                    }
                )
                print(f"[{scenario_id}][TOOL]\n{observation}\n", flush=True)
                messages.append(
                    ToolMessage(
                        content=observation,
                        tool_call_id=call.get("id", "tool-call"),
                    )
                )

            trace[:] = trace_local

            pending = live_utils.expected_command_gaps(state)
            if pending:
                reminder = (
                    "STATUS: Pending required reconnaissance or workflow commands. Next recommended action: "
                    f"`{pending[0]}` (still outstanding: {', '.join(pending)})."
                )
                state.add_status(reminder, phase="reminder")
                trace_local.append(
                    {
                        "timestamp": live_utils.timestamp(),
                        "role": "user",
                        "phase": "reminder",
                        "content": reminder,
                    }
                )
                messages.append(HumanMessage(content=reminder))

            return {
                "messages": messages,
                "trace": trace_local,
                "status": "continue",
            }

        if sanitized_content.strip().startswith(DONE_TOKEN):
            trace_local.append(
                {
                    "timestamp": live_utils.timestamp(),
                    "role": "assistant",
                    "phase": "completion",
                    "content": sanitized_content,
                }
            )
            trace[:] = trace_local
            return {
                "messages": messages,
                "trace": trace_local,
                "status": "done",
                "final_report": sanitized_content,
            }

        # No tool call and not DONE -> send gentle reminder.
        reminder = "STATUS: Awaiting the next command to continue the workflow."
        state.add_status(reminder, phase="reminder")
        trace_local.append(
            {
                "timestamp": live_utils.timestamp(),
                "role": "user",
                "phase": "reminder",
                "content": reminder,
            }
        )
        messages.append(HumanMessage(content=reminder))
        trace[:] = trace_local
        return {
            "messages": messages,
            "trace": trace_local,
            "status": "continue",
        }

    def reporter_node(current_state: Dict[str, Any]) -> Dict[str, Any]:
        trace_local = list(current_state.get("trace", []))
        final_report = current_state.get("final_report", "")
        if final_report:
            trace_local.append(
                {
                    "timestamp": live_utils.timestamp(),
                    "role": "assistant",
                    "phase": "report",
                    "content": final_report,
                }
            )
        trace[:] = trace_local
        return {
            "final_report": final_report,
            "trace": trace_local,
            "status": "completed",
        }

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reporter", reporter_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("reporter", END)

    def route_execution(current_state: Dict[str, Any]) -> str:
        return "report" if current_state.get("status") == "done" else "executor"

    graph.add_conditional_edges("executor", route_execution, {"executor": "executor", "report": "reporter"})

    compiled_graph = graph.compile()

    initial_state = {
        "trace": trace,
        "messages": [],
        "status": "start",
    }
    try:
        final_state = compiled_graph.invoke(initial_state, config={"recursion_limit": 120})
        error_message = None
    except GraphRecursionError as exc:
        final_state = {"final_report": "", "trace": trace}
        error_message = str(exc)

    evaluation = live_utils.evaluate_scenario(state)
    if error_message:
        evaluation.setdefault("issues", []).append(error_message)
        evaluation["passed"] = False

    result_payload = {
        "scenario_id": scenario_id,
        "workspace": str(state.current_dir),
        "output_dir": str(output_dir),
        "final_report": final_state.get("final_report"),
        "issues": evaluation.get("issues", []),
        "passed": evaluation.get("passed", False),
        "commands": [r.to_dict() for r in state.command_results],
        "status_updates": evaluation.get("status_updates", []),
        "trace": final_state.get("trace", []),
    }

    trace_path = output_dir / "trace.jsonl"
    with trace_path.open("w", encoding="utf-8") as handle:
        for entry in result_payload["trace"]:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(result_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[INFO] Stored artifacts for {scenario_id} under {output_dir}", flush=True)

    if not keep_workspace:
        live_utils.cleanup_workspace(workspace)

    if result_payload["issues"]:
        print(f"[FAIL] {scenario_id} – {result_payload['issues']}")
    else:
        print(f"[PASS] {scenario_id}")

    return result_payload


def handle_directory_change(
    state: live_utils.ScenarioState,
    command: str,
    stream_callback,
) -> str:
    try:
        state.logger.log(command, task_id=state.scenario_id)
    except ValueError as exc:
        message = f"Command rejected by safety policy: {exc}"
        stream_callback("stderr", message + "\n")
        result = CommandResult(
            command=command,
            cwd=str(state.current_dir),
            returncode=None,
            stdout="",
            stderr=message,
            start_time=time.time(),
            end_time=time.time(),
            blocked=True,
            error=str(exc),
        )
        state.record_result(result)
        return message

    target = command.split(maxsplit=1)[1].strip()
    start_time = time.time()
    if target.startswith("~"):
        target_path = Path(target).expanduser()
    else:
        candidate = Path(target)
        target_path = candidate if candidate.is_absolute() else (state.current_dir / candidate)
    target_path = target_path.resolve()

    if not target_path.exists():
        message = f"Directory {target_path} does not exist."
        result = CommandResult(
            command=command,
            cwd=str(state.current_dir),
            returncode=1,
            stdout="",
            stderr=message,
            start_time=start_time,
            end_time=time.time(),
        )
        state.record_result(result)
        stream_callback("stderr", message + "\n")
        return f"cd failed: {message}"

    state.change_directory(target_path)
    message = f"Changed directory to {target_path}"
    result = CommandResult(
        command=command,
        cwd=str(target_path),
        returncode=0,
        stdout=message,
        stderr="",
        start_time=start_time,
        end_time=time.time(),
    )
    state.record_result(result)
    stream_callback("stdout", message + "\n")
    return message


def main() -> int:
    args = parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

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
    )

    documents = load_documents()
    scenarios = load_scenarios(args.requests_path, args.max_prompts)

    results: List[Dict[str, Any]] = []
    for scenario in scenarios:
        result = run_scenario(
            scenario,
            documents=documents,
            planner_llm=planner_llm,
            executor_llm=executor_llm,
            keep_workspace=args.keep_workspace,
        )
        results.append(result)

    overall = {
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
    }
    summary_payload = {
        "scenarios": [
            {"id": item["scenario_id"], "passed": item["passed"], "issues": item["issues"]}
            for item in results
        ],
        **overall,
    }
    summary_path = OUTPUT_ROOT / "summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[DONE] {overall}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
