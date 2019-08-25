cmake_minimum_required(VERSION 3.0)
project(resource_test)

set(CMAKE_CXX_STANDARD 11)

# compile resources
find_package( PythonInterp 3.0 REQUIRED )
set(RES_GEN_COMMAND ${PYTHON_EXECUTABLE} ${PROJECT_SOURCE_DIR}/../resource-builder.py ${PROJECT_SOURCE_DIR}/res)
execute_process(COMMAND ${RES_GEN_COMMAND})

include_directories(
        ${PROJECT_SOURCE_DIR}
        ${PROJECT_SOURCE_DIR}/res/build/include
)

file(GLOB all_SRCS
        ${PROJECT_SOURCE_DIR}/*.cpp
        ${PROJECT_SOURCE_DIR}/res/build/src/resources.cpp
        )

if( WIN32 )
    # On windows resources are compiled with source by using .rc file
    add_executable(${PROJECT_NAME} ${all_SRCS} ${PROJECT_SOURCE_DIR}/res/win.rc)
else()
    add_executable(${PROJECT_NAME} ${all_SRCS})

    # On linux object files are created and should be linked with your executable
    file(GLOB all_OBJS ${PROJECT_SOURCE_DIR}/res/build/objs/*.o)
    target_link_libraries(${PROJECT_NAME} ${all_OBJS})
endif()
