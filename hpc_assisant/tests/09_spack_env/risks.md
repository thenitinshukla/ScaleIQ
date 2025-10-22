# Risks and mitigations – Suite 09_spack_env

- **Missing spack executable**
  - *Signal*: Detection succeeds but concretize command fails with `spack: command not found`.
  - *Action*: Document fallback to mocked outputs; request module load instructions from suite 03.

- **Complex manifests**
  - *Signal*: `spack.yaml` contains matrices or conditional specs not handled by parser.
  - *Action*: Flag the plan with `notes` and require manual review before promotion.

- **Activation side effects**
  - *Signal*: Environment activation modifies global shell state unexpectedly.
  - *Action*: Use subshells or `modulecmd`-style evaluation to confine mutations; log all changes.

- **Credential leakage**
  - *Signal*: Spack mirrors or build caches contain tokens in URLs.
  - *Action*: Apply redaction rules before writing plans or logs.

- **Stale concretize output**
  - *Signal*: Reusing old concretization results mismatched with current manifest.
  - *Action*: Include manifest checksum in `spack_plan.json` and invalidate cache when it changes.
