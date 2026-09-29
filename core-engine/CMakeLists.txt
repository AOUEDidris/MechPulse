cmake_minimum_required(VERSION 3.15)
project(VibrationGuardEngine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

file(GLOB SOURCES 
    "src/*.cpp"
)

add_executable(vibration_engine ${SOURCES})

if(WIN32)
    target_link_libraries(vibration_engine PRIVATE ws2_32)
endif()
