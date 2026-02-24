cmake_minimum_required(VERSION 3.10)
project(SAGA_Architect VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define directories
set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src)
set(DEPS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/deps)

# Include directories
include_directories(${SRC_DIR})
include_directories(${DEPS_DIR})
# nlohmann/json is expected to be in deps or available via system
# For scaffolding, we'll assume it's in deps/nlohmann

# Add main executable
add_executable(saga_architect
    ${SRC_DIR}/main.cpp
    ${SRC_DIR}/core/Types.h
    ${SRC_DIR}/map/VoronoiGen.cpp
    ${SRC_DIR}/simulation/AutoPopulate.cpp
    ${SRC_DIR}/io/Exporter.cpp
)

# Target-specific settings
target_include_directories(saga_architect PRIVATE ${SRC_DIR})
