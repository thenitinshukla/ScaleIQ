# Local API specification

## Purpose
Expose a local API (Unix socket or localhost HTTP) for orchestrating agent actions programmatically.

## Responsibilities
- Serve endpoints defined in `tests/23_cli_api_surface/data/api_schema.yaml`.
- Validate requests/responses against OpenAPI schemas.
- Integrate with planner/executor components while enforcing sandbox restrictions.

## Interface
```python
class LocalAPI:
    def __init__(self, app: Any, logger: AuditLogger | None = None): ...
    def create_app(self) -> Any: ...
    def start(self, host: str = \"127.0.0.1\", port: int = 8080) -> None: ...
```

### `create_app`
- Builds routes `/plan`, `/execute`, `/status`.
- Ensures payload validation matches `tests/23_cli_api_surface/expected/api_openapi_fragment.yaml`.

### `start`
- Launches server in restricted environment; may use Uvicorn/FastAPI or Flask.
- Hooks into audit logging for each request.

## Security
- Document authentication (token or local-only binding).
- Limit to loopback / Unix socket by default.
