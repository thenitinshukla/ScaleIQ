# Risks and mitigations – Suite 10_conda_env

- **Environment name clashes**
  - *Signal*: `conda env create` fails because an environment with the same name already exists.
  - *Action*: Use hashed prefixes or `conda env remove` with confirmation; document reuse strategy in metadata.

- **Shell contamination**
  - *Signal*: After running tests, parent shell shows modified `PATH` or prompt.
  - *Action*: Prefer `conda run` over `conda activate`; verify environment diff resets after command.

- **Slow environment creation**
  - *Signal*: Test stalls while solving dependencies.
  - *Action*: Allow caching of solved environments; log solving time and provide fallback instructions.

- **Unavailable conda binary**
  - *Signal*: `conda` not found on system.
  - *Action*: Document requirement to load Anaconda module or use Micromamba; provide mock execution instructions.

- **Unredacted credentials**
  - *Signal*: Channels include tokens or credentials.
  - *Action*: Redact sensitive strings before logging metadata.
