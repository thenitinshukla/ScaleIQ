# Risks and mitigations – Suite 04_build_cmake

- **Missing modules or compilers**
  - *Signal*: CMake fails to locate compilers or modules.
  - *Action*: Re-run suite 03 to ensure modules are loaded; document missing dependencies in the audit log.

- **Dirty build directory**
  - *Signal*: Configuration picks up stale cache entries.
  - *Action*: Remove or isolate previous `build/` directories; enforce clean workspace creation per run.

- **Generator mismatch**
  - *Signal*: CMake selects the wrong generator (e.g., Xcode) leading to build failure.
  - *Action*: Force `-G "Unix Makefiles"` or site-preferred generator in `data/cmake_flags.md`.

- **Parallel build saturation**
  - *Signal*: Build fails due to resource limits when using high `--parallel`.
  - *Action*: Tune parallelism according to `data/build_parallelism.md` and document fallback to serial builds.

- **Artifact drift**
  - *Signal*: Produced binaries differ between runs without code changes.
  - *Action*: Track checksums and environment metadata; investigate non-deterministic sources (timestamps, embedded paths).
