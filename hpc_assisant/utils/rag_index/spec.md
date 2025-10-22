# RAG indexing specification

## Purpose
Ingest local documentation, generate embeddings, and persist searchable indices for retrieval.

## Responsibilities
- Collect documents from approved directories (`.docs/`, etc.) according to inclusion rules.
- Normalize text, compute hashes, and maintain an ingest manifest.
- Batch requests to the embedding endpoint (see `.env` configuration) and capture latency metrics.
- Store vector indices (e.g., FAISS) along with metadata linking vectors to documents.

## Interface
```python
class RAGIndexer:
    def __init__(self, config: dict, client: EmbeddingClient): ...
    def build_index(self, paths: list[Path]) -> dict: ...
    def save_index(self, index: Any, metadata: dict, dest: Path) -> dict: ...
```

### `build_index`
- Follows steps from `tests/13_rag_index/plan.md`.
- Returns info shaped like `tests/13_rag_index/expected/index_metadata_template.json`.
- Records ingestion manifest and latency stats.

### `save_index`
- Persists index files to `runs/<timestamp>/rag/index/`.
- Writes manifest matching `tests/13_rag_index/expected/ingest_manifest_template.json`.
- Logs checksums for reproducibility.

## Logging
- Use audit logging (Suite 16) for each batch with sanitized payload hashes.
- Store latency metrics in `latency_report.json` as per expected template.
