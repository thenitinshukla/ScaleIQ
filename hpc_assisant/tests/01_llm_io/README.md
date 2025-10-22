# Suite 01 – LLM I/O

This suite validates the minimal integration with the local LLM service: every request must include the `/nothink` directive, outputs must be sanitized from `<think>` tags, and tool calls must follow the expected JSON schema.

## Suite contents
- **T-0101-nothink-param** – Check that the vLLM request includes `/nothink` in the instruction payload.
- **T-0102-strip-think** – Ensure `<think>...</think>` tags are removed while keeping the operational text intact.
- **T-0103-toolcall-schema** – Confirm the model response can be parsed into a tool call with compliant `name` and `arguments` fields.

## Shared prerequisites
- Endpoint and credentials configured as established in suite 00.
- Access to `curl` or an equivalent allow-listed client.
- Sample data under `data/` prepared in the required formats (prompt, raw responses).

## High-level manual procedure
1. Issue a model call using the prompt in `data/prompt_nothink.txt`.
2. Save the raw response to `runs/<timestamp>/llm_raw.json` as described in `plan.md`.
3. Apply the sanitization steps outlined in `expected/sanitized_output.txt` and compare the outcome.
4. Extract the tool call from the sanitized content and validate it against the JSON schema in `expected/tool_call_schema.json`.

## Supporting documentation
- `plan.md` details the step-by-step workflow and promotion criteria for `utils/llm_client`.
- `data/` provides prompts and specimen responses to reproduce the test cases.
- `expected/` houses examples of correct requests, sanitized outputs, and the JSON schema.
- `risks.md` highlights failure modes (missing sanitization, schema violations, HTTP errors) and mitigations.
