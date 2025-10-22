# Sanitization rules

- Remove every substring that starts with `<think>` and ends with the matching `</think>`, including newlines.
- Trim leading/trailing whitespace after removal.
- Preserve JSON formatting and escape sequences.
- Record the original length and sanitized length in the audit log.
