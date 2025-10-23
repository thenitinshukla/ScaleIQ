#!/usr/bin/env python3
"""Build a documentation vector store and exercise retrieval-augmented prompting."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import chromadb
from chromadb.api.models.Collection import Collection
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "llm" / "system_prompt.md"
DOCS_PATH = PROJECT_ROOT / "hpc_documentation"
OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs"
VECTOR_STORE_PATH = Path(__file__).resolve().parent / "vector_store"
COLLECTION_NAME = "hpc_documentation"
THINK_SOURCE = "/nothink"
DEFAULT_EMBED_BATCH_SIZE = 8
DEFAULT_EMBED_TIMEOUT = 60.0
DEFAULT_LLM_TIMEOUT = 120.0


def load_env_variable(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value


def chunk_markdown(path: Path, max_lines: int = 40, overlap: int = 8) -> Iterable[Tuple[str, int, str]]:
    """Yield (chunk_text, starting_line, section_title) tuples for a markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []

    headings: List[str] = []
    current_heading = "Introduction"
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip() or current_heading
        headings.append(current_heading)

    start = 0
    total_lines = len(lines)
    while start < total_lines:
        end = min(total_lines, start + max_lines)
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()
        if chunk_text:
            heading_index = min(start, len(headings) - 1)
            yield chunk_text, start + 1, headings[heading_index]
        if end >= total_lines:
            break
        start = max(0, end - overlap)
        if start >= total_lines:
            break


def ensure_collection(force_rebuild: bool, embeddings: OpenAIEmbeddings, batch_size: int) -> Collection:
    """Create or rebuild the Chroma collection backing the documentation store."""
    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_PATH))

    if force_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            # Deleting a non-existent collection raises; ignore to allow idempotent rebuilds.
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if force_rebuild or collection.count() == 0:
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        for doc_path in sorted(DOCS_PATH.glob("*.md")):
            for chunk, line_start, section in chunk_markdown(doc_path):
                chunk_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                doc_id = f"{doc_path.stem}-{line_start}-{chunk_hash[:12]}"
                documents.append(chunk)
                metadatas.append(
                    {
                        "source": doc_path.name,
                        "section": section,
                        "line_start": line_start,
                        "hash": chunk_hash,
                    }
                )
                ids.append(doc_id)

        if not documents:
            raise RuntimeError(f"No markdown documents found under {DOCS_PATH}")

        existing_count = collection.count()
        if existing_count > 0:
            # Replace the collection contents to avoid stale embeddings.
            existing_ids = collection.get()["ids"]
            if existing_ids:
                collection.delete(ids=existing_ids)

        if batch_size <= 0:
            batch_size = 4

        def batched(sequence: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
            for i in range(0, len(sequence), size):
                yield sequence[i : i + size]

        payload = list(zip(ids, documents, metadatas))
        total_batches = (len(payload) + batch_size - 1) // batch_size
        print(f"[INFO] Embedding {len(payload)} chunks ({total_batches} batches, size={batch_size})", flush=True)
        for chunk in batched(payload, batch_size):
            chunk_ids, chunk_docs, chunk_meta = zip(*chunk)
            try:
                chunk_embeddings = embeddings.embed_documents(list(chunk_docs))
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"Failed to embed a batch of {len(chunk_docs)} documents. "
                    f"Try reducing EMBED_BATCH_SIZE. Original error: {exc}"
                ) from exc

            if len(chunk_embeddings) != len(chunk_docs):
                raise RuntimeError("Embedding service returned unexpected vector count for a batch")

            collection.add(
                ids=list(chunk_ids),
                documents=list(chunk_docs),
                embeddings=chunk_embeddings,
                metadatas=list(chunk_meta),
            )
        print("[INFO] Embedding complete; collection populated.", flush=True)

    return collection


def strip_think(text: str) -> str:
    return text.replace("<think>", "").replace("</think>", "").strip()


def has_citation(text: str, metadatas: List[Dict[str, Any]]) -> bool:
    for meta in metadatas:
        if not meta:
            continue
        source = meta.get("source")
        line_start = meta.get("line_start")
        if not source or line_start is None:
            continue
        citation = f"{source}:{line_start}"
        if citation in text:
            return True
    return False


def run_queries(
    collection: Collection,
    embeddings: OpenAIEmbeddings,
    llm: ChatOpenAI,
    queries: List[Dict[str, str]],
    output_dir: Path,
) -> List[Dict[str, Any]]:
    """Execute retrieval + generation for each query and persist debug payloads."""
    run_records: List[Dict[str, Any]] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()

    for entry in queries:
        task_id = entry.get("id", "unknown")
        query_text = entry.get("query", "")
        if not query_text:
            print(f"[WARN] Skipping query '{task_id}' because text is empty", file=sys.stderr)
            continue

        print(f"[INFO] Running retrieval for '{task_id}'", flush=True)
        print("  -> Embedding query...", flush=True)
        query_embedding = embeddings.embed_query(query_text)
        print("  -> Query embedding ready; fetching similar chunks...", flush=True)
        results = collection.query(query_embeddings=[query_embedding], n_results=5)
        print("  -> Retrieved candidate chunks.", flush=True)

        def first_or_empty(matrix: Any) -> List[Any]:
            if not matrix:
                return []
            first = matrix[0]
            return first or []

        retrieved_docs = first_or_empty(results.get("documents"))
        retrieved_metadatas = first_or_empty(results.get("metadatas"))
        distances = first_or_empty(results.get("distances"))

        retrieval_payload: List[Dict[str, Any]] = []
        for doc_text, metadata, distance in zip(retrieved_docs, retrieved_metadatas, distances):
            if not doc_text:
                continue
            metadata = metadata or {}
            source = metadata.get("source", "unknown")
            line_start = metadata.get("line_start", 0)
            section = metadata.get("section", "")
            similarity = 1.0 - distance if distance is not None else None
            citation = f"{source}:{line_start}"
            retrieval_payload.append(
                {
                    "citation": citation,
                    "section": section,
                    "score": similarity,
                    "text": doc_text,
                }
            )

        human_payload = {
            "query": query_text,
            "retrieved": retrieval_payload,
            "instructions": "Use the retrieved context. Cite sources as [source:line] for factual claims.",
        }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=THINK_SOURCE
                + "\n\nCONTEXT:\n"
                + json.dumps(human_payload, indent=2, ensure_ascii=False)
                + "\n\nTASK:\n"
                + query_text
            ),
        ]

        print("  -> Sending prompt to LLM...", flush=True)
        response = llm.invoke(messages)
        print("  -> LLM response received.", flush=True)
        raw_content = response.content or ""
        sanitized_content = strip_think(raw_content)
        citation_present = has_citation(sanitized_content, retrieved_metadatas)
        print(
            f"[INFO] LLM completed '{task_id}' (citations found: {citation_present})",
            flush=True,
        )

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
        }

        output_path = output_dir / f"{task_id}.json"
        output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[INFO] Stored retrieval response for '{task_id}' at {output_path.relative_to(PROJECT_ROOT)}")

        run_records.append(
            {
                "id": task_id,
                "query": query_text,
                "output_file": str(output_path.relative_to(PROJECT_ROOT)),
                "citation_present": citation_present,
                "retrieved_count": len(retrieval_payload),
            }
        )

    return run_records


def load_queries(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing queries file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Queries file must contain a list of objects")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval-augmented prompts against the HPC docs.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force a rebuild of the documentation vector store from source Markdown.",
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
        help="Override the batch size used for embedding chunks (defaults to env EMBED_BATCH_SIZE or 8).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_base = load_env_variable("VLLM_API_BASE")
    api_key = load_env_variable("VLLM_API_KEY")
    model_name = load_env_variable("VLLM_MODEL_NAME")
    embedding_api_base = load_env_variable("VLLM_EMBEDDING_API_BASE")
    embedding_model_name = load_env_variable("VLLM_EMBEDDING_NAME")

    embed_timeout = float(os.getenv("EMBED_TIMEOUT", str(DEFAULT_EMBED_TIMEOUT)))
    embeddings = OpenAIEmbeddings(
        openai_api_base=embedding_api_base,
        openai_api_key=api_key,
        model=embedding_model_name,
        max_retries=2,
        timeout=embed_timeout,
    )

    embed_batch_size = args.embed_batch_size
    if embed_batch_size is None:
        embed_batch_size = int(os.getenv("EMBED_BATCH_SIZE", str(DEFAULT_EMBED_BATCH_SIZE)))
    collection = ensure_collection(
        force_rebuild=args.rebuild,
        embeddings=embeddings,
        batch_size=embed_batch_size,
    )

    llm_timeout = float(os.getenv("LLM_TIMEOUT", str(DEFAULT_LLM_TIMEOUT)))
    llm = ChatOpenAI(
        openai_api_base=api_base,
        openai_api_key=api_key,
        model=model_name,
        temperature=0.2,
        max_tokens=1200,
        timeout=llm_timeout,
    )

    queries = load_queries(args.queries_path)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_dir = OUTPUT_ROOT / timestamp
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    run_records = run_queries(collection, embeddings, llm, queries, output_dir)

    summary = {
        "generated_at": timestamp,
        "model": model_name,
        "embedding_model": embedding_model_name,
        "queries_file": str(args.queries_path.relative_to(PROJECT_ROOT)),
        "runs": run_records,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Retrieval test outputs stored under {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
