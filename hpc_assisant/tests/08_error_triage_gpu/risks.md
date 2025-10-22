# Risks and mitigations – Suite 08_error_triage_gpu

- **Architecture name drift**
  - *Signal*: Logs reference new SM or GFX identifiers not covered by existing rules.
  - *Action*: Update the architecture mapping table and expand regex patterns; add fallback advice pointing to `nvidia-smi`/`rocm-smi` discovery.

- **Mixed CPU/GPU errors**
  - *Signal*: Logs contain both compile and GPU-specific issues causing ambiguous matches.
  - *Action*: Prioritize GPU rules after compile rules, but ensure evidence snippets clearly indicate GPU-related lines.

- **Incorrect advice for legacy hardware**
  - *Signal*: Suggested `-gencode` or `--offload-arch` does not exist on cluster nodes.
  - *Action*: Tie advice to policy metadata (suite 18) and present alternate architecture values.

- **Redaction gaps**
  - *Signal*: Paths to proprietary CUDA installs leak in triage output.
  - *Action*: Reuse redactors from suite 06 before emitting JSON.

- **False positives from warnings**
  - *Signal*: Informational warnings contain phrases like "unsupported" without failing the build.
  - *Action*: Require fatal keywords (`fatal`, `error`) and non-zero exit hints before classifying.
