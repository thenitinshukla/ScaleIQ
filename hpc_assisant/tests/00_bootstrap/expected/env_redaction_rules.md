# Masking rules for `env.json`

- Mask every value that includes tokens such as `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, or `API`.
- Replace the sensitive portion with `***MASKED***` while keeping useful prefixes intact (e.g., keep `https://api.local/v1`, but turn `Bearer <token>` into `Bearer ***MASKED***`).
- Preserve original keys to aid debugging.
- Add a `masking_strategy` field to the audit log entry indicating the approach used (`pattern_based` or `manual_review`).
