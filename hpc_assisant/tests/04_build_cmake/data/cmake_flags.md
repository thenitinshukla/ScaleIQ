# Recommended CMake flags

- `-DCMAKE_BUILD_TYPE=Release`
- `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`
- `-DCMAKE_C_COMPILER=$(which gcc)`
- `-DCMAKE_CXX_COMPILER=$(which g++)`
- Add site-specific toolchain files if required (`-DCMAKE_TOOLCHAIN_FILE=/path/to/toolchain.cmake`).
