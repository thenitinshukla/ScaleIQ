"""Shared utilities for the HPC assistant test harnesses."""

from .env import (
    EmbeddingSettings,
    LLMSettings,
    get_project_root,
    get_system_prompt,
    load_embedding_settings,
    load_env_variable,
    load_llm_settings,
)
from .llm import (
    build_chat_llm,
    build_embeddings_client,
    build_messages,
    strip_think,
)
from .retrieval import (
    DocumentChunk,
    RetrievedChunk,
    build_vector_store,
    contains_citation,
    load_markdown_chunks,
    query_collection,
)
from .tools import (
    CommandLogger,
    build_emit_command_tool,
)

__all__ = [
    "EmbeddingSettings",
    "LLMSettings",
    "get_project_root",
    "get_system_prompt",
    "load_embedding_settings",
    "load_env_variable",
    "load_llm_settings",
    "build_chat_llm",
    "build_embeddings_client",
    "build_messages",
    "strip_think",
    "DocumentChunk",
    "RetrievedChunk",
    "build_vector_store",
    "contains_citation",
    "load_markdown_chunks",
    "query_collection",
    "CommandLogger",
    "build_emit_command_tool",
]
