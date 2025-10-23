#!/usr/bin/env python3
"""Send a batch of requests to the LLM using LangChain ChatOpenAI."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "llm/system_prompt.md"
REQUESTS_PATH = Path(__file__).resolve().parent / "requests.json"
THINK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def load_env_variable(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value


def strip_think(text: str) -> str:
    return THINK_PATTERN.sub("", text).strip()


def main() -> int:
    api_base = load_env_variable("VLLM_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model_name = load_env_variable("VLLM_MODEL_NAME")

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    context_pack: Dict[str, Any] = {}
    requests_data: List[Dict[str, Any]] = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))

    llm = ChatOpenAI(
        openai_api_base=api_base,
        openai_api_key=api_key,
        model=model_name,
        temperature=0.2,
        max_tokens=1200,
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(__file__).resolve().parent / "outputs" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    for entry in requests_data:
        task_id = entry.get("id", "unknown")
        task = entry.get("task", "")
        if not task:
            print(f"[WARN] Skipping request '{task_id}' because task is empty", file=sys.stderr)
            continue

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="/nothink\n\nCONTEXT:\n" + json.dumps(context_pack) + "\n\nTASK:\n" + task),
        ]
        response = llm.invoke(messages)
        raw_content = response.content
        sanitized_content = strip_think(raw_content or "")

        debug_payload = {
            "request": {
                "system_prompt": system_prompt,
                "context": context_pack,
                "task": task,
            },
            "response_raw": raw_content,
            "response_sanitized": sanitized_content,
        }

        output_path = output_dir / f"{task_id}.json"
        output_path.write_text(json.dumps(debug_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[INFO] Stored LangChain response for '{task_id}' at {output_path.relative_to(PROJECT_ROOT)}")

    summary_path = output_dir / "summary.json"
    summary = {
        "generated_at": timestamp,
        "model": model_name,
        "requests_file": str(REQUESTS_PATH.relative_to(PROJECT_ROOT)),
        "responses": [f"outputs/{timestamp}/{entry.get('id', 'unknown')}.json" for entry in requests_data],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] LangChain responses stored under {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
