# Parsing notes for `module spider`

- Capture the "Versions" lines and split on whitespace.
- Record "Description" text to provide context for each module family.
- Normalize family names to lowercase (e.g., `GCC` → `gcc`).
- Store output as:
  ```json
  {
    "family": "gcc",
    "versions": ["11.2.0", "12.1.0"],
    "description": "GNU Compiler Collection"
  }
  ```
- Include a `retrieved_at` timestamp at the root of the snapshot.
