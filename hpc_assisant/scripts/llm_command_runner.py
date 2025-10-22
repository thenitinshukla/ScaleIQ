#!/usr/bin/env python3
"""Generate shell commands via the local LLM and optionally execute them."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    from langchain.chat_models import ChatOpenAI  # type: ignore

from langchain.schema import HumanMessage, SystemMessage

from utils.config import ConfigProvider


SYSTEM_PROMPT = """You are an HPC assistant. For each user request, respond with a JSON object\nwith a single key \"command\" whose value is an array of strings representing the shell\ncommand to run. Only produce valid JSON.\n"""


def build_llm() -> ChatOpenAI:
    config = ConfigProvider()
    values = config.load()
    base_url = values.get("VLLM_API_BASE") or values.get("OPENAI_API_BASE")
    api_key = values.get("VLLM_API_KEY") or values.get("OPENAI_API_KEY")
    model_name = values.get("VLLM_MODEL_NAME") or values.get("OPENAI_API_MODEL")
    if not (base_url and api_key and model_name):
        raise RuntimeError("Missing API configuration for LLM (check .env)")
    return ChatOpenAI(
        openai_api_base=base_url,
        openai_api_key=api_key,
        model=model_name,
        temperature=0.0,
    )


def request_command(task: str) -> list[str]:
    llm = build_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Task: {task}"),
    ]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise RuntimeError(f"LLM response not valid JSON: {response.content}") from exc
    command = data.get("command")
    if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
        raise RuntimeError("LLM did not return a command array")
    return command  # type: ignore


def execute_command(command: list[str]) -> int:
    print("Executing:", " ".join(command))
    result = subprocess.run(command, check=False)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate shell commands via LLM")
    parser.add_argument("task", help="Natural language description of the desired shell command")
    parser.add_argument("--execute", action="store_true", help="Execute the generated command")
    args = parser.parse_args()

    command = request_command(args.task)
    print(json.dumps({"command": command}, indent=2))
    if args.execute:
        code = execute_command(command)
        sys.exit(code)


if __name__ == "__main__":
    main()
