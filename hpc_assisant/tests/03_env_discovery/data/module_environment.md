# Module environment assumptions

- `MODULEPATH` points to `/opt/modulefiles` and site-specific trees under `/apps/modulefiles`.
- Lmod version 8.x or higher is available.
- Default modules loaded: `StdEnv`
- Module evaluation must occur via `modulecmd python` to persist updates inside the agent process.
