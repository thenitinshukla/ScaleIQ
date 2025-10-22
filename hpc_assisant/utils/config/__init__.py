"""Configuration utilities for the HPC assistant tests."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_CANDIDATES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / ".env",
    PROJECT_ROOT / ".env.example",
    PROJECT_ROOT.parent / ".env.example",
)

SENSITIVE_KEY_PATTERN = re.compile(r"(token|secret|password|key|api)", re.IGNORECASE)
SENSITIVE_VALUE_PATTERN = re.compile(r"(token|secret|password|bearer|apikey)", re.IGNORECASE)


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            data[key] = value
    return data


def _mask_value(key: str, value: str) -> str:
    if not value:
        return value
    if SENSITIVE_KEY_PATTERN.search(key) or SENSITIVE_VALUE_PATTERN.search(value):
        prefix = value[:4]
        suffix = value[-4:] if len(value) > 8 else ""
        return f"{prefix}***MASKED***{suffix}"
    return value


@dataclass
class ConfigProvider:
    """Load `.env` configuration and expose masked views."""

    env_candidates: Iterable[Path] = field(default_factory=lambda: DEFAULT_ENV_CANDIDATES)
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ.copy())
    required_keys: tuple[str, ...] = (
        "VLLM_API_BASE",
        "VLLM_API_KEY",
        "VLLM_MODEL_NAME",
    )
    alternative_keys: tuple[tuple[str, ...], ...] = (
        ("VLLM_EMBEDDING_MODEL", "VLLM_EMBEDDING_NAME"),
    )

    def __post_init__(self) -> None:
        self._env_path: Path | None = None
        self._values: dict[str, str] = {}
        self._masked: dict[str, str] = {}
        self._loaded = False

    @property
    def env_path(self) -> Path:
        if self._env_path is None:
            for candidate in self.env_candidates:
                if candidate.exists():
                    self._env_path = candidate
                    break
            else:
                raise FileNotFoundError("Unable to locate .env or .env.example")
        return self._env_path

    def load(self) -> dict[str, str]:
        file_values = _parse_env_file(self.env_path)
        merged: MutableMapping[str, str] = dict(file_values)
        for key, value in self.environ.items():
            if key in merged:
                merged[key] = value
        self._values = dict(merged)
        self._masked = {}
        self._loaded = True
        self._validate()
        return self._values

    def get(self, key: str, default: str | None = None) -> str | None:
        if not self._loaded:
            self.load()
        return self._values.get(key, default)

    def masked(self) -> dict[str, str]:
        if not self._loaded:
            self.load()
        if not self._masked:
            self._masked = {key: _mask_value(key.lower(), value) for key, value in self._values.items()}
        return self._masked

    def as_dict(self) -> dict[str, str]:
        if not self._loaded:
            self.load()
        return dict(self._values)

    def _validate(self) -> None:
        missing = [key for key in self.required_keys if not self._values.get(key)]
        if missing:
            raise ValueError(f"Missing required configuration keys: {', '.join(sorted(missing))}")
        for group in self.alternative_keys:
            if not any(self._values.get(key) for key in group):
                raise ValueError(
                    "Missing required configuration key: expected at least one of "
                    + ", ".join(group)
                )
