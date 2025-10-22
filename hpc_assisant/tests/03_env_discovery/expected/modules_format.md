# Module snapshot format

- JSON root keys:
  - `retrieved_at`: ISO8601 timestamp.
  - `modules`: list of module families with `family`, `versions`, `description`.
- Versions array should be sorted newest to oldest.
- Optional fields:
  - `source`: command used to gather information (e.g., `"module spider"`).
  - `notes`: clarifications about missing versions or aliases.
