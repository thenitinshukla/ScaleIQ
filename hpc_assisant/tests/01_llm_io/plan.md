# Execution plan – Suite 01_llm_io

## Goal
Prove the agent can interact with the vLLM endpoint using `/nothink`, sanitize raw responses, and parse tool calls into a structured format ready for execution.

## Tests included
1. **T-0101-nothink-param**
   - **Input**: prompt in `data/prompt_nothink.txt`; reference request body in `expected/request_payload.json`.
   - **Steps**:
     1. Build a request including `/nothink` in the instruction field.
     2. Send the request using an allow-listed client (e.g., `curl`) or simulate it via documented steps.
     3. Capture the full HTTP payload in `runs/<timestamp>/llm_request.json`.
   - **Done when**:
     - The recorded payload matches the structure and directive in `expected/request_payload.json`.
     - Audit log contains an entry for the request (HTTP status, latency, endpoint).

2. **T-0102-strip-think**
   - **Input**: raw model response with `<think>` tags in `data/llm_raw_with_think.txt`.
   - **Steps**:
     1. Apply the sanitization rules from `expected/sanitize_rules.md`.
     2. Save the cleaned output to `runs/<timestamp>/llm_sanitized.txt`.
   - **Done when**:
     - No `<think>` tags remain.
     - Operational text matches `expected/sanitized_output.txt`.
     - Audit log notes the sanitization action and character count delta.

3. **T-0103-toolcall-schema**
   - **Input**: sanitized output from T-0102 or the sample in `data/toolcall_candidate.json`.
   - **Steps**:
     1. Parse the tool call into `name` and `arguments`.
     2. Validate against `expected/tool_call_schema.json`.
     3. Store the parsed structure under `runs/<timestamp>/tool_call.json`.
   - **Done when**:
     - JSON is valid and contains all required fields.
     - Arguments conform to the documented types and required keys.

## Promotion to utils/
- **utils/llm_client**
  - `build_request(nothink=True)` – guarantees the directive is appended.
  - `sanitize_response(raw_text)` – strips `<think>` blocks and normalizes whitespace.
  - `parse_tool_call(text)` – extracts tool call JSON with validation.
  - `retry_policy(meta)` – documents backoff strategy for transient HTTP failures.

Promote once all tests pass and the documentation describes:
- Error handling for HTTP status codes.
- Required headers and auth derived from `.env`.
- Logging expectations (request/response hashes, sanitized excerpts only).
