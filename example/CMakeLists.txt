cmake_minimum_required(VERSION 3.1)
project(resource_example)

set(CMAKE_CXX_STANDARD 11)

# compile resources
find_package( PythonInterp 3.0 REQUIRED )
execute_process(COMMAND ${PYTHON_EXECUTABLE}
        ${PROJECT_SOURCE_DIR}/../resource-builder.py #path to python script that builds resources
        ${PROJECT_SOURCE_DIR}/res                    #work directory where resources are stored
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(resource_example main.cpp)

#resource will be compiled in res/build folder (it is specified in res/resources.json)
#we only need to add it as subdirectory and link to created library
#name of the library is specified in resources.json
add_subdirectory(res/build)
target_link_libraries(resource_example PRIVATE ResourceBuilder::ResourceBuilder)
