# Build-system indicators

- `CMakeLists.txt` → classify as `cmake`; list supporting modules such as `cmake`, `ctest`.
- `Makefile` or `makefile` → classify as `make`; identify default target.
- `setup.py`, `pyproject.toml` → flag for future Python support (mark as `unknown` for now but note evidence).
- Presence of `.cu` files → add `CUDA` to language hints.
- Presence of `.f90`, `.f95` → add `Fortran` to language hints.
