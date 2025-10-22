"""Minimal wrapper for the local LLM endpoint."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

import requests

from utils.config import ConfigProvider

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


class LLMClient:
    """Simple HTTP client that talks to the local vLLM /chat/completions API."""

    def __init__(self) -> None:
        config = ConfigProvider()
        values = config.load()
        self.base_url = values.get("VLLM_API_BASE")
        self.api_key = values.get("VLLM_API_KEY")
        self.model = values.get("VLLM_MODEL_NAME")
        if not all([self.base_url, self.api_key, self.model]):
            raise RuntimeError("Missing VLLM configuration in .env")

    def invoke(self, system_prompt: str, context_pack: Dict[str, Any], task: str) -> Dict[str, Any]:
        payload = self._build_payload(system_prompt, context_pack, task)
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()
        message = raw["choices"][0]["message"]
        if message.get("content"):
            message["content"] = self._strip_think(message["content"])
        return raw

    def _build_payload(self, system_prompt: str, context_pack: Dict[str, Any], task: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "/nothink\n\nCONTEXT:\n"
                + json.dumps(context_pack)
                + "\n\nTASK:\n"
                + task,
            },
        ]
        return {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200,
            "stream": False,
        }

    @staticmethod
    def _strip_think(text: str) -> str:
        return THINK_PATTERN.sub("", text).strip()


__all__ = ["LLMClient"]
