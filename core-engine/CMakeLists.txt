cmake_minimum_required(VERSION 3.15)
project(MechPulseEngine
    VERSION 1.0.0
    DESCRIPTION "MechPulse Industrial Vibration Monitoring & Edge DSP Engine"
    LANGUAGES CXX
)

# Enforce C++17 Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Collect source files and headers using GLOB
file(GLOB_RECURSE ENGINE_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
)

file(GLOB_RECURSE ENGINE_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/*.hpp
)

# Executable target
add_executable(MechPulseEngine
    ${ENGINE_SOURCES}
    ${ENGINE_HEADERS}
)

target_include_directories(MechPulseEngine PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link Windows Socket Library (ws2_32) on Windows platforms
if(WIN32)
    target_link_libraries(MechPulseEngine PRIVATE ws2_32)
endif()

# Compiler optimization and warning settings
if(MSVC)
    target_compile_options(MechPulseEngine PRIVATE /W4 /O2 /permissive-)
else()
    target_compile_options(MechPulseEngine PRIVATE -Wall -Wextra -O3 -pthread)
endif()
