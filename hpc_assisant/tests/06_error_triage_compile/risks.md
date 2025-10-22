# Risks and mitigations – Suite 06_error_triage_compile

- **Overlapping regex rules**
  - *Signal*: Multiple rules fire on the same log segment.
  - *Action*: Order rules by priority and ensure the classifier records all matches with clear precedence.

- **Low confidence scores**
  - *Signal*: Confidence falls below the threshold, leaving the agent unsure.
  - *Action*: Add additional context patterns or fallback advice prompting manual review.

- **Incorrect remediation advice**
  - *Signal*: Suggested module or include path does not resolve the issue.
  - *Action*: Validate advice against site module names; include alternative steps in the returned payload.

- **Unmasked sensitive paths**
  - *Signal*: Logs leak user home directories or private paths.
  - *Action*: Redact sensitive substrings before persisting triage outputs.

- **Unsupported compiler messages**
  - *Signal*: New compiler versions change error wording.
  - *Action*: Update `data/invalid_flag.log` and expand regex coverage when new variants are observed.
