#!/usr/bin/env python3
"""Exercise retrieval-augmented prompting with command tool logging."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure the workspace root and project parent are importable.
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[1]
PROJECT_PARENT = SCRIPT_DIR.parents[2]
for candidate in (str(WORKSPACE_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

try:
    from hpc_assistant.utils import env as env_utils
    from hpc_assistant.utils import llm as llm_utils
    from hpc_assistant.utils import retrieval as retrieval_utils
    from hpc_assistant.utils import tools as tool_utils
except ModuleNotFoundError:
    from utils import env as env_utils
    from utils import llm as llm_utils
    from utils import retrieval as retrieval_utils
    from utils import tools as tool_utils

PROJECT_ROOT = env_utils.get_project_root()
DOCS_PATH = PROJECT_ROOT / "hpc_documentation"
OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs"
VECTOR_STORE_PATH = Path(__file__).resolve().parent / "vector_store"
COLLECTION_NAME = "hpc_documentation"
THINK_DIRECTIVE = "/nothink"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run retrieval-augmented prompts and capture tool calls.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuilding the documentation vector store from source markdown.",
    )
    parser.add_argument(
        "--queries-path",
        type=Path,
        default=Path(__file__).resolve().parent / "queries.json",
        help="Path to the JSON file containing retrieval queries.",
    )
    parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=None,
        help="Override the embedding batch size (defaults to env EMBED_BATCH_SIZE or 8).",
    )
    return parser.parse_args()


def load_queries(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing queries file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Queries file must contain a list of query objects.")
    return data


def run_queries(
    *,
    queries: List[Dict[str, str]],
    collection,
    embeddings_client,
    llm_client,
    system_prompt: str,
    output_dir: Path,
    command_logger: tool_utils.CommandLogger,
) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_records: List[Dict[str, Any]] = []

    for entry in queries:
        task_id = entry.get("id", "unknown")
        query_text = entry.get("query", "")
        if not query_text:
            print(f"[WARN] Skipping query '{task_id}' because text is empty", file=sys.stderr)
            continue

        print(f"[INFO] Running retrieval for '{task_id}'", flush=True)
        retrieved_chunks = retrieval_utils.query_collection(
            collection=collection,
            embeddings=embeddings_client,
            query=query_text,
            top_k=5,
        )
        print(f"  -> Retrieved {len(retrieved_chunks)} candidate chunks.", flush=True)

        retrieval_payload = [
            {
                "citation": chunk.citation,
                "section": chunk.section,
                "score": chunk.score,
                "text": chunk.text,
            }
            for chunk in retrieved_chunks
        ]

        context_payload = {
            "query": query_text,
            "retrieved": retrieval_payload,
            "instructions": (
                "Use the retrieved context. Cite sources as [source:line] for factual claims. "
                "Propose shell commands via the emit_command tool."
            ),
        }

        messages = llm_utils.build_messages(
            system_prompt,
            query_text,
            context=context_payload,
            think_directive=THINK_DIRECTIVE,
        )

        command_logger.clear()
        print("  -> Sending prompt to LLM...", flush=True)
        response = llm_client.invoke(messages)
        print("  -> LLM response received.", flush=True)

        raw_content = response.content or ""
        sanitized_content = llm_utils.strip_think(raw_content)
        citation_present = retrieval_utils.contains_citation(sanitized_content, retrieved_chunks)
        print(f"[INFO] LLM completed '{task_id}' (citations found: {citation_present})", flush=True)

        output_payload = {
            "request": {
                "query": query_text,
                "retrieved": retrieval_payload,
            },
            "response_raw": json.loads(response.model_dump_json()),
            "response_sanitized": {
                "content": sanitized_content,
                "citation_present": citation_present,
            },
            "commands": command_logger.entries,
        }

        output_path = output_dir / f"{task_id}.json"
        output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[INFO] Stored tool-retrieval response for '{task_id}' at {output_path.relative_to(PROJECT_ROOT)}")

        run_records.append(
            {
                "id": task_id,
                "query": query_text,
                "output_file": str(output_path.relative_to(PROJECT_ROOT)),
                "citation_present": citation_present,
                "retrieved_count": len(retrieval_payload),
                "commands_logged": len(command_logger.entries),
            }
        )

    return run_records


def main() -> int:
    args = parse_args()

    llm_settings = env_utils.load_llm_settings()
    embedding_settings = env_utils.load_embedding_settings()
    if args.embed_batch_size is not None:
        embedding_settings.batch_size = args.embed_batch_size

    embeddings_client = llm_utils.build_embeddings_client(embedding_settings)
    system_prompt = env_utils.get_system_prompt()

    print("[INFO] Loading documentation chunks...", flush=True)
    doc_chunks = retrieval_utils.load_markdown_chunks(DOCS_PATH)
    print(f"[INFO] Loaded {len(doc_chunks)} chunks from {DOCS_PATH.name}", flush=True)

    def progress_callback(batch_number: int, total_batches: int) -> None:
        print(f"[INFO] Embedding batch {batch_number}/{total_batches}", flush=True)

    collection = retrieval_utils.build_vector_store(
        chunks=doc_chunks,
        embeddings=embeddings_client,
        persist_directory=VECTOR_STORE_PATH,
        collection_name=COLLECTION_NAME,
        force_rebuild=args.rebuild,
        batch_size=embedding_settings.batch_size,
        progress_callback=progress_callback,
    )

    output_timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_dir = OUTPUT_ROOT / output_timestamp
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    command_log_path = output_dir / "commands.jsonl"
    command_logger = tool_utils.CommandLogger(command_log_path)
    emit_command_tool = tool_utils.build_emit_command_tool(command_logger)

    llm_client = llm_utils.build_chat_llm(llm_settings, tools=[emit_command_tool])
    queries = load_queries(args.queries_path)

    run_records = run_queries(
        queries=queries,
        collection=collection,
        embeddings_client=embeddings_client,
        llm_client=llm_client,
        system_prompt=system_prompt,
        output_dir=output_dir,
        command_logger=command_logger,
    )

    summary = {
        "generated_at": output_timestamp,
        "model": llm_settings.model,
        "embedding_model": embedding_settings.model,
        "queries_file": str(args.queries_path.relative_to(PROJECT_ROOT)),
        "runs": run_records,
        "commands_log": str(command_log_path.relative_to(PROJECT_ROOT)),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Tool-retrieval outputs stored under {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
