# LLM client specification

## Purpose
Provide a stable interface for issuing requests to the vLLM endpoint, sanitizing responses, and extracting tool calls.

## Responsibilities
- Assemble request payloads with `/nothink` directive by default.
- Handle authentication using values from `ConfigProvider`.
- Sanitize model outputs by removing `<think>` blocks.
- Parse tool calls and validate against the schema in `tests/01_llm_io/expected/tool_call_schema.json`.
- Implement retry strategy for transient HTTP errors.

## Interface
```python
class LLMClient:
    def __init__(self, config: ConfigProvider, session: httpx.Client | None = None): ...
    def build_request(self, prompt: str, nothink: bool = True) -> dict: ...
    def invoke(self, prompt: str) -> dict: ...
    def sanitize_response(self, raw_text: str) -> str: ...
    def parse_tool_call(self, sanitized_text: str) -> dict: ...
```

## Retry policy
- Retry up to 3 times on 429 or 5xx with exponential backoff (1s, 2s, 4s).
- Log each retry attempt with status code and delay.

## Logging
- Store request/response hashes in `events.jsonl`.
- Persist sanitized completion under `runs/<timestamp>/llm_sanitized.txt`.
