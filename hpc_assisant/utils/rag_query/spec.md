# RAG query specification

## Purpose
Retrieve relevant documents from the embedding index and assemble context packs for LLM prompts.

## Responsibilities
- Load indices created by `RAGIndexer`.
- Execute similarity searches with configurable top-k and thresholds.
- Score and record relevance ratings.
- Build context blocks with citations, enforcing token limits.

## Interface
```python
class RAGQuery:
    def __init__(self, index: Any, metadata: dict): ...
    def retrieve(self, query: str, k: int, config: dict) -> dict: ...
    def make_context(self, hits: list[dict], max_tokens: int) -> dict: ...
```

### `retrieve`
- Applies configuration in `tests/14_rag_retrieve/data/retrieve_config.json`.
- Returns structure matching `tests/14_rag_retrieve/expected/topk_results_template.json`.
- Records latency and scoring metrics.

### `make_context`
- Follows packaging rules from `tests/14_rag_retrieve/data/context_guidelines.md`.
- Produces context block/metadata similar to templates in `expected/`.

## Logging
- Log query parameters, latency, and top-k document IDs.
- Capture manual relevance ratings for evaluation runs.
