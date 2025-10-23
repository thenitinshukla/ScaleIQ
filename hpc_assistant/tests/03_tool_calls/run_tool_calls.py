#!/usr/bin/env python3
"""Exercise LangChain tool-calling with a command preview tool."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "llm/system_prompt.md"
REQUESTS_PATH = Path(__file__).resolve().parent / "requests.json"
OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs"
COMMANDS_FILE = Path(__file__).resolve().parent / "outputs" / "commands_log.jsonl"
THINK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)

_command_buffer: list[Dict[str, Any]] = []


def load_env_variable(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value


def strip_think(text: str) -> str:
    return THINK_PATTERN.sub("", text).strip()


def log_command(command: str) -> str:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command,
    }
    _command_buffer.append(entry)
    return "Command logged"


def main() -> int:
    api_base = load_env_variable("VLLM_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model_name = load_env_variable("VLLM_MODEL_NAME")

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    requests_data = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))

    tool = Tool(
        name="emit_command",
        description="Record a shell command proposed by the assistant. Do not execute it.",
        func=log_command,
    )

    llm = ChatOpenAI(
        openai_api_base=api_base,
        openai_api_key=api_key,
        model=model_name,
        temperature=0.2,
        max_tokens=1200,
    ).bind_tools([tool])

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_dir = OUTPUT_ROOT / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    COMMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)

    for entry in requests_data:
        task_id = entry.get("id", "unknown")
        task = entry.get("task", "")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="/nothink\n\nCONTEXT:\n{}\n\nTASK:\n" + task),
        ]
        response = llm.invoke(messages)

        raw_response = json.loads(response.model_dump_json())
        sanitized_response = json.loads(response.model_dump_json())
        sanitized_content = strip_think(response.content or "")
        sanitized_response["content"] = sanitized_content

        output_path = output_dir / f"{task_id}.json"
        output_payload = {
            "request": {
                "system_prompt": system_prompt,
                "task": task,
            },
            "response_raw": raw_response,
            "response_sanitized": sanitized_response,
        }
        output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[INFO] Stored tool-call response for '{task_id}' at {output_path.relative_to(PROJECT_ROOT)}")

        if _command_buffer:
            with COMMANDS_FILE.open("a", encoding="utf-8") as handle:
                for item in _command_buffer:
                    item_with_task = dict(item)
                    item_with_task["task_id"] = task_id
                    handle.write(json.dumps(item_with_task) + "\n")
            _command_buffer.clear()

    print(f"[DONE] Tool-call responses stored under {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
