# Hybrid Build Sample

This repository supports both Make and CMake workflows.

## Option 1 – CMake (preferred on Leonardo)
```
cmake -S . -B build
cmake --build build -j 8
```

## Option 2 – Make
```
make all
```

Please choose the toolchain that best respects module availability.
