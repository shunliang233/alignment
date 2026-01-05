# Project
cmake_minimum_required(VERSION 3.16)
project(millepede 
    VERSION 1.0.0
    DESCRIPTION "Track parameters to Alignment parameters conversion tool chain."
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

# Find ROOT - Auto include path by components
find_package(ROOT REQUIRED COMPONENTS Core RIO Tree)

# Add argparse subdirectory
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

# Executable 1root2bin
add_executable(1convert src/main.cpp src/Mille.cpp)
target_include_directories(1convert PRIVATE include)
target_link_libraries(1convert PRIVATE 
    ROOT::Core 
    ROOT::RIO 
    ROOT::Tree
    argparse::argparse
)
# Excutable 2pede

# Excutable 3fixanotherlayers
add_executable(3fixanotherlayers src/Fixfromstep1.cpp)

# Excutable 4pede2

# Excutable 5reconvert
add_executable(5.1PedetoDB_ss src/PedetoDB_ss.cpp)
add_executable(5.2add_param src/add_param.cpp)

# Configuration summary
message(STATUS "=== Mille Converter Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "ROOT version: ${ROOT_VERSION}")
message(STATUS "argparse dir: ${CMAKE_CURRENT_SOURCE_DIR}/argparse")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "=====================================")

# Installation: 安装所有可执行文件到 bin 目录
install(TARGETS
    1convert
    3fixanotherlayers
    5.1PedetoDB_ss
    5.2add_param
    RUNTIME DESTINATION bin
    COMPONENT Runtime
)


# Configure Python script
set(MILLEPEDE_BIN_DIR "${CMAKE_INSTALL_PREFIX}/bin")
set(MILLEPEDE_TXT_DIR "${CMAKE_INSTALL_PREFIX}/txt")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/millepede_temp.py"
    "${CMAKE_CURRENT_BINARY_DIR}/millepede.py"
    @ONLY
)
# Install configured Python script
install(PROGRAMS "${CMAKE_CURRENT_BINARY_DIR}/millepede.py"
    DESTINATION bin
    COMPONENT Runtime
)