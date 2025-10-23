"""Utilities for building and querying the documentation vector store."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from langchain_openai import OpenAIEmbeddings


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    section: str
    line_start: int
    hash: str


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    citation: str
    section: str
    score: Optional[float]


ProgressCallback = Callable[[int, int], None]


def chunk_markdown(path: Path, *, max_lines: int = 40, overlap: int = 8) -> List[DocumentChunk]:
    """Split a markdown file into overlapping chunks ready for embedding."""
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

    chunks: List[DocumentChunk] = []
    start = 0
    total_lines = len(lines)
    while start < total_lines:
        end = min(total_lines, start + max_lines)
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()
        if chunk_text:
            heading_index = min(start, len(headings) - 1)
            section = headings[heading_index]
            line_start = start + 1
            chunk_hash = hashlib.sha256(
                f"{path}:{line_start}:{chunk_text}".encode("utf-8"),
            ).hexdigest()
            chunks.append(
                DocumentChunk(
                    text=chunk_text,
                    source=path.name,
                    section=section,
                    line_start=line_start,
                    hash=chunk_hash,
                )
            )
        if end >= total_lines:
            break
        start = max(0, end - overlap)
        if start >= total_lines:
            break
    return chunks


def load_markdown_chunks(
    root: Path,
    *,
    max_lines: int = 40,
    overlap: int = 8,
) -> List[DocumentChunk]:
    """Collect chunks for every markdown file under ``root``."""
    all_chunks: List[DocumentChunk] = []
    for file_path in sorted(root.glob("*.md")):
        all_chunks.extend(chunk_markdown(file_path, max_lines=max_lines, overlap=overlap))
    return all_chunks


def build_vector_store(
    *,
    chunks: Sequence[DocumentChunk],
    embeddings: OpenAIEmbeddings,
    persist_directory: Path,
    collection_name: str,
    force_rebuild: bool = False,
    batch_size: int = 8,
    progress_callback: Optional[ProgressCallback] = None,
) -> Collection:
    """Create or update a persistent Chroma collection with the supplied chunks."""
    persist_directory.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_directory))

    if force_rebuild:
        try:
            client.delete_collection(collection_name)
        except Exception:
            # Removing a non-existent collection raises; ignore to allow idempotent rebuilds.
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    if not force_rebuild and collection.count() > 0:
        return collection

    if not chunks:
        raise RuntimeError("No documentation chunks were provided to the vector store builder")

    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    if batch_size <= 0:
        batch_size = 4

    payload = [
        (
            f"{chunk.source}-{chunk.line_start}-{chunk.hash[:12]}",
            chunk.text,
            {
                "source": chunk.source,
                "section": chunk.section,
                "line_start": chunk.line_start,
                "hash": chunk.hash,
            },
        )
        for chunk in chunks
    ]

    total_batches = (len(payload) + batch_size - 1) // batch_size

    def batched(sequence: Sequence, size: int) -> Iterable[Sequence]:
        for index in range(0, len(sequence), size):
            yield sequence[index : index + size]

    for batch_number, batch in enumerate(batched(payload, batch_size), start=1):
        batch_ids, batch_docs, batch_meta = zip(*batch)
        embeddings_list = embeddings.embed_documents(list(batch_docs))
        if len(embeddings_list) != len(batch_docs):
            raise RuntimeError("Embedding service returned an unexpected vector count")
        collection.add(
            ids=list(batch_ids),
            documents=list(batch_docs),
            embeddings=embeddings_list,
            metadatas=list(batch_meta),
        )
        if progress_callback:
            progress_callback(batch_number, total_batches)

    return collection


def query_collection(
    *,
    collection: Collection,
    embeddings: OpenAIEmbeddings,
    query: str,
    top_k: int = 5,
) -> List[RetrievedChunk]:
    """Return the top matching documentation chunks for ``query``."""
    query_embedding = embeddings.embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    distances = (results.get("distances") or [[]])[0] or []

    retrieved: List[RetrievedChunk] = []
    for doc_text, metadata, distance in zip(documents, metadatas, distances):
        if not doc_text:
            continue
        metadata = metadata or {}
        source = metadata.get("source", "unknown")
        line_start = metadata.get("line_start", 0)
        section = metadata.get("section", "")
        citation = f"{source}:{line_start}"
        score = 1.0 - distance if distance is not None else None
        retrieved.append(
            RetrievedChunk(
                text=doc_text,
                citation=citation,
                section=section,
                score=score,
            )
        )
    return retrieved


def contains_citation(text: str, chunks: Sequence[RetrievedChunk]) -> bool:
    """Determine whether the response text cites one of the retrieved chunks."""
    for chunk in chunks:
        if chunk.citation and chunk.citation in text:
            return True
    return False
