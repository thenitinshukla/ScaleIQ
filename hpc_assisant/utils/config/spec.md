# ConfigProvider specification

## Purpose
Expose configuration values sourced from `.env` and environment variables with masking and validation.

## Responsibilities
- Load `.env` file from the project root.
- Allow overrides from process environment variables.
- Mask sensitive values when logging.
- Validate presence of required keys (`VLLM_API_BASE`, `VLLM_API_KEY`, `VLLM_MODEL_NAME`, `VLLM_EMBEDDING_MODEL`).

## Interface
```python
class ConfigProvider:
    def __init__(self, env_file: Path | None = None): ...
    def load(self) -> dict[str, str]: ...
    def get(self, key: str, default: str | None = None) -> str | None: ...
    def masked(self) -> dict[str, str]: ...
    def validate(self) -> None: ...
```

## Logging
- Emit `runs/<timestamp>/env.json` using `masked()` values.
- Record masking strategy (`pattern_based`, `manual_review`).
