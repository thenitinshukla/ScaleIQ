"""Environment helpers for the HPC assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class MissingEnvironmentVariable(RuntimeError):
    """Raised when a required environment variable is not present."""


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "llm" / "system_prompt.md"


@dataclass
class LLMSettings:
    api_base: str
    api_key: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 1200
    timeout: Optional[float] = None


@dataclass
class EmbeddingSettings:
    api_base: str
    api_key: str
    model: str
    timeout: Optional[float] = None
    batch_size: int = 8


def load_env_variable(key: str) -> str:
    """Return the value of ``key`` or raise if it is missing."""
    value = os.getenv(key)
    if not value:
        raise MissingEnvironmentVariable(f"Environment variable {key} is required but not set")
    return value


def _read_float_env(key: str, default: Optional[float]) -> Optional[float]:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:  # noqa: BLE001
        raise ValueError(f"Environment variable {key} must be a float, got: {raw}") from exc


def _read_int_env(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # noqa: BLE001
        raise ValueError(f"Environment variable {key} must be an integer, got: {raw}") from exc


def load_llm_settings(
    *,
    default_temperature: float = 0.2,
    default_max_tokens: int = 1200,
    default_timeout: Optional[float] = None,
) -> LLMSettings:
    """Load standard ChatLLM configuration from the environment."""
    api_base = load_env_variable("VLLM_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model = load_env_variable("VLLM_MODEL_NAME")
    temperature = _read_float_env("LLM_TEMPERATURE", default_temperature)
    max_tokens = _read_int_env("LLM_MAX_TOKENS", default_max_tokens)
    timeout = _read_float_env("LLM_TIMEOUT", default_timeout)
    return LLMSettings(
        api_base=api_base,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def load_embedding_settings(
    *,
    default_batch_size: int = 8,
    default_timeout: Optional[float] = None,
) -> EmbeddingSettings:
    """Load embedding configuration from the environment."""
    api_base = load_env_variable("VLLM_EMBEDDING_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model = load_env_variable("VLLM_EMBEDDING_NAME")
    timeout = _read_float_env("EMBED_TIMEOUT", default_timeout)
    batch_size = _read_int_env("EMBED_BATCH_SIZE", default_batch_size)
    return EmbeddingSettings(
        api_base=api_base,
        api_key=api_key,
        model=model,
        timeout=timeout,
        batch_size=batch_size,
    )


def get_project_root() -> Path:
    """Return the repository root used by the assistant."""
    return PROJECT_ROOT


def get_system_prompt(path: Optional[Path] = None) -> str:
    """Read and return the canonical system prompt."""
    prompt_path = path or SYSTEM_PROMPT_PATH
    return prompt_path.read_text(encoding="utf-8").strip()
