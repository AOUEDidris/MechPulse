cmake_minimum_required(VERSION 3.15)
project(MechPulseEngine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(MechPulseEngine engine.cpp)

if(WIN32)
    target_link_libraries(MechPulseEngine PRIVATE ws2_32)
endif()

if(MSVC)
    target_compile_options(MechPulseEngine PRIVATE /W4 /O2)
else()
    target_compile_options(MechPulseEngine PRIVATE -Wall -Wextra -O3)
endif()
