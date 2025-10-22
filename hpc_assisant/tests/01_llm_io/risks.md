# Risks and mitigations – Suite 01_llm_io

- **Directive omitted**
  - *Signal*: Recorded request body lacks `/nothink`.
  - *Action*: Update request builder to append the directive by default; re-run T-0101.

- **Residual `<think>` blocks**
  - *Signal*: Sanitized file still contains `<think>` tags or malformed output.
  - *Action*: Refine the sanitization procedure; ensure tests cover nested tags and multiline cases.

- **Invalid tool call JSON**
  - *Signal*: JSON schema validation fails or `arguments` is not a structured object.
  - *Action*: Add stricter parsing with descriptive errors; confirm the schema in `expected/tool_call_schema.json` is up to date.

- **Logging sensitive payloads**
  - *Signal*: Full raw completion stored in plain text logs.
  - *Action*: Redact or hash large prompts/completions; log only metadata and sanitized snippets.

- **HTTP instability**
  - *Signal*: Frequent 429/5xx responses during testing.
  - *Action*: Document retry and cooldown behaviour in `utils/llm_client` before promotion.
