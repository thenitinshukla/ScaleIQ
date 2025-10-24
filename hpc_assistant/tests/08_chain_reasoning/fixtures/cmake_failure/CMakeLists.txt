cmake_minimum_required(VERSION 3.21)
project(failure_demo LANGUAGES CXX)

find_package(CUDA REQUIRED)

add_executable(demo src/main.cu)
set_target_properties(demo PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
