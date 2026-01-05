# Project
cmake_minimum_required(VERSION 3.16)
project(analysis 
    VERSION 1.0.0
    DESCRIPTION "Analyse root files."
    LANGUAGES CXX
)

# Install prefix
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}" CACHE PATH "Install prefix" FORCE)
    message(STATUS "Using default install prefix: ${CMAKE_INSTALL_PREFIX}")
else()
    message(STATUS "Using custom install prefix: ${CMAKE_INSTALL_PREFIX}")
endif()

# Export compile commands for IDE support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Strict c++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0 -Wall -Wextra)
else()
    add_compile_options(-O3 -DNDEBUG)
endif()

# Set default Build Type to "Release" if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS Debug Release RelWithDebInfo MinSizeRel)
endif()

# Find ROOT
find_package(ROOT REQUIRED COMPONENTS Core RIO Tree Hist)

# Find argparse
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/argparse/CMakeLists.txt")
    # 禁用 argparse 的测试和示例
    set(ARGPARSE_BUILD_TESTS OFF CACHE BOOL "Disable argparse tests")
    set(ARGPARSE_BUILD_SAMPLES OFF CACHE BOOL "Disable argparse samples")
    message(STATUS "Start argparse/CMakeLists.txt")
    add_subdirectory(argparse)
    message(STATUS "Finish argparse/CMakeLists.txt")
else()
    message(FATAL_ERROR 
        "argparse subdirectory not found. Please:\n"
        "  git submodule update --init"
    )
endif()

# 全局包含 include 目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# Executable analysis
add_executable(analysis src/main.cpp src/Analyser.cpp)
target_link_libraries(analysis PRIVATE 
    ROOT::Core 
    ROOT::RIO
    ROOT::Tree
    ROOT::Hist
    argparse::argparse
)

# Configuration summary
message(STATUS "=== Mille Converter Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "ROOT version: ${ROOT_VERSION}")
message(STATUS "argparse dir: ${CMAKE_CURRENT_SOURCE_DIR}/argparse")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "=====================================")

# Installation
install(TARGETS
    analysis
    RUNTIME DESTINATION bin
    COMPONENT Runtime
)
