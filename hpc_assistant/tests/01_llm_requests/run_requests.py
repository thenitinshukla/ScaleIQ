#!/usr/bin/env python3
"""Send a batch of requests to the local LLM endpoint using raw HTTP."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

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


def build_payload(system_prompt: str, context_pack: Dict[str, Any], task: str, model: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "/nothink\n\nCONTEXT:\n" + json.dumps(context_pack) + "\n\nTASK:\n" + task,
        },
    ]
    return {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1200,
        "stream": False,
    }


def main() -> int:
    api_base = load_env_variable("VLLM_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model_name = load_env_variable("VLLM_MODEL_NAME")

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    context_pack: Dict[str, Any] = {}
    requests_data: List[Dict[str, Any]] = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(__file__).resolve().parent / "outputs" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    headers = {"Authorization": f"Bearer {api_key}"}

    for entry in requests_data:
        task_id = entry.get("id", "unknown")
        task = entry.get("task", "")
        if not task:
            print(f"[WARN] Skipping request '{task_id}' because task is empty", file=sys.stderr)
            continue

        payload = build_payload(system_prompt, context_pack, task, model_name)
        response = session.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()
        sanitized = json.loads(json.dumps(raw))  # deep copy
        message = sanitized["choices"][0]["message"]
        content = message.get("content", "")
        message["content"] = strip_think(content)

        debug_payload = {
            "request": payload,
            "response_raw": raw,
            "response_sanitized": sanitized,
        }

        output_path = output_dir / f"{task_id}.json"
        output_path.write_text(json.dumps(debug_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[INFO] Stored response for '{task_id}' at {output_path.relative_to(PROJECT_ROOT)}")

    summary_path = output_dir / "summary.json"
    summary = {
        "generated_at": timestamp,
        "model": model_name,
        "requests_file": str(REQUESTS_PATH.relative_to(PROJECT_ROOT)),
        "responses": [f"outputs/{timestamp}/{entry.get('id', 'unknown')}.json" for entry in requests_data],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Responses stored under {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
