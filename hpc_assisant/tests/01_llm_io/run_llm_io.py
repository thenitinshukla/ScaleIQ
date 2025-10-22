"""Harness for suite 01 (LLM I/O) covering T-0101..T-0103."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ConfigProvider
from utils.paths import RunPaths

DATA_DIR = Path(__file__).resolve().parent / "data"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"
SANITIZE_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def sanitize_think_blocks(text: str) -> tuple[str, int]:
    cleaned, count = SANITIZE_PATTERN.subn("", text)
    return cleaned.strip(), count


def validate_tool_call(payload: dict) -> dict:
    if "tool_call" not in payload or not isinstance(payload["tool_call"], dict):
        raise ValueError("Missing tool_call dict in payload")
    tool_call = payload["tool_call"]
    name = tool_call.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("tool_call.name must be a non-empty string")
    arguments = tool_call.get("arguments")
    if not isinstance(arguments, dict):
        raise ValueError("tool_call.arguments must be an object")
    return {
        "name": name,
        "argument_keys": sorted(arguments.keys()),
    }


def main() -> int:
    config = ConfigProvider()
    run_paths = RunPaths.create()

    # T-0101 – Build request with /nothink directive
    prompt_path = DATA_DIR / "prompt_nothink.txt"
    prompt = load_text(prompt_path)
    request = {
        "model": config.get("VLLM_MODEL_NAME"),
        "input": [
            {"role": "system", "content": "/nothink"},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0.0,
    }
    request_path = run_paths.run_dir / "llm_request.json"
    run_paths.write_json(request_path, request)
    run_paths.append_event(
        {
            "step": "T-0101-nothink-param",
            "action": "build_request",
            "request_path": str(request_path.relative_to(PROJECT_ROOT)),
            "model": request["model"],
            "has_nothink": any(msg.get("content") == "/nothink" for msg in request["input"]),
        }
    )

    # T-0102 – Sanitize <think> blocks
    raw_text = load_text(DATA_DIR / "llm_raw_with_think.txt")
    sanitized, removed = sanitize_think_blocks(raw_text)
    sanitized_path = run_paths.run_dir / "llm_sanitized.txt"
    sanitized_path.write_text(sanitized + "\n", encoding="utf-8")
    expected_sanitized = load_text(EXPECTED_DIR / "sanitized_output.txt")
    run_paths.append_event(
        {
            "step": "T-0102-strip-think",
            "action": "sanitize_response",
            "sanitized_path": str(sanitized_path.relative_to(PROJECT_ROOT)),
            "blocks_removed": removed,
            "matches_expected": sanitized == expected_sanitized,
        }
    )

    # T-0103 – Validate tool call JSON
    try:
        payload = json.loads(sanitized)
    except json.JSONDecodeError as exc:
        run_paths.append_event(
            {
                "step": "T-0103-toolcall-schema",
                "action": "parse_tool_call",
                "status": "error",
                "error": str(exc),
            }
        )
        print(f"[llm_io] ERROR parsing tool call: {exc}", file=sys.stderr)
        return 1

    validation = validate_tool_call(payload)
    tool_call_path = run_paths.run_dir / "tool_call.json"
    run_paths.write_json(tool_call_path, payload)
    run_paths.append_event(
        {
            "step": "T-0103-toolcall-schema",
            "action": "validate_tool_call",
            "tool_call_path": str(tool_call_path.relative_to(PROJECT_ROOT)),
            "name": validation["name"],
            "argument_keys": validation["argument_keys"],
        }
    )

    print(f"[llm_io] Run artifacts stored in {run_paths.run_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
