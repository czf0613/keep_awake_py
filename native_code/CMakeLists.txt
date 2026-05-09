cmake_minimum_required(VERSION 3.20)
project(keep_awake_native C)

# This CMakeLists.txt is only for IDE code hints (e.g. CLion, VS Code).
# Do NOT use CMake to build this project. Use setup.py instead.

find_package(Python3 REQUIRED COMPONENTS Development)

add_library(_native_api SHARED
    src/ext.c
    src/pm_macos.c
)

target_include_directories(_native_api PRIVATE
    ${Python3_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(_native_api PRIVATE
    ${Python3_LIBRARIES}
    "-framework CoreFoundation"
    "-framework IOKit"
)
