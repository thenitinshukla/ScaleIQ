cmake_minimum_required(VERSION 3.18)
project(sample_hpc_project LANGUAGES CXX)

add_executable(sample src/main.cpp)
target_compile_features(sample PRIVATE cxx_std_17)
