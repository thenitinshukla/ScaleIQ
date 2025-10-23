"""Helpers for constructing LLM clients and messages."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Sequence

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .env import EmbeddingSettings, LLMSettings

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def strip_think(text: Optional[str]) -> str:
    """Remove `<think>` sections emitted by compliant models."""
    if not text:
        return ""
    return THINK_PATTERN.sub("", text).strip()


def build_chat_llm(settings: LLMSettings, tools: Optional[Sequence[BaseTool]] = None) -> ChatOpenAI:
    """Create a ChatOpenAI client with the standard defaults."""
    client = ChatOpenAI(
        openai_api_base=settings.api_base,
        openai_api_key=settings.api_key,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout,
    )
    if tools:
        client = client.bind_tools(list(tools))
    return client


def build_embeddings_client(settings: EmbeddingSettings) -> OpenAIEmbeddings:
    """Construct an embedding client configured for the vLLM endpoint."""
    return OpenAIEmbeddings(
        openai_api_base=settings.api_base,
        openai_api_key=settings.api_key,
        model=settings.model,
        timeout=settings.timeout,
        max_retries=2,
    )


def build_messages(
    system_prompt: str,
    task: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    think_directive: str = "/nothink",
) -> List[BaseMessage]:
    """Compose the standard message pair used by the harness."""
    context_payload = context if context is not None else {}
    human_content = (
        f"{think_directive}\n\n"
        f"CONTEXT:\n{json.dumps(context_payload, indent=2, ensure_ascii=False)}\n\n"
        f"TASK:\n{task}"
    )
    return [
        SystemMessage(content=system_prompt.strip()),
        HumanMessage(content=human_content),
    ]
