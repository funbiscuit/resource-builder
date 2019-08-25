Resource Builder for C++
------------------------

A simple cross-platform resource builder for C++ programs.
Works on Linux, Windows and MacOS (10.7 and higher). Python 3.x is required.

Tested with latest Manjaro Linux, Windows 7/10 and MacOS 10.14

On Linux uses `objcopy` to generate
object files that will link with your code.

On Windows `.rc` file is generated to be compiled with your code.

On MacOS uses `ld` to create object files that will link with your code.
Internally uses `getsectiondata()` that's why MacOS 10.6 and older are not supported.


How to use
-------------
It is the simplest to use this builder with CMake project.

Suppose you have `resource-builder.py` located at `./libs/resource-builder/resource-builder.py`.

In CMakeLists.txt add following code:

~~~
find_package( PythonInterp 3.0 REQUIRED )

#if you put your resource files not in ./res folder make changes here
set(RES_GEN_COMMAND ${PYTHON_EXECUTABLE} ${PROJECT_SOURCE_DIR}/libs/resource-builder/resource-builder.py ${PROJECT_SOURCE_DIR}/res)
execute_process(COMMAND ${RES_GEN_COMMAND})

#your need to add res/build/include as include dir:
include_directories(${PROJECT_SOURCE_DIR}/res/build/include)

# In your add_executable call add generated source (suppose all other sources are stored in all_SRCS variable
if( WIN32 )
    add_executable(${PROJECT_NAME} ${all_SRCS} ${PROJECT_SOURCE_DIR}/res/build/src/resources.cpp ${PROJECT_SOURCE_DIR}/res/build/src/win.rc)
else()
    # On Linux and Mac OS don't forget to link generated object files with executable
    file(GLOB res_OBJS ${PROJECT_SOURCE_DIR}/res/build/objs/*.o)
    add_executable(${PROJECT_NAME} ${all_SRCS} ${PROJECT_SOURCE_DIR}/res/build/src/resources.cpp)
    target_link_libraries(${PROJECT_NAME} ${res_OBJS})
endif()
~~~

You need to place `resources.json` inside `res` directory in your project root. This file has following format:
~~~
{
  // in resources array you should specify relative path to all your resources
  "resources" : [
    "./icons/r*/*.png", //you can use * to create patterns. basically, this can be any regex (used with fnmatch)
    "./txt/*.txt"
  ],
  // in output you should store the name of build folder. all generated files are placed there
  "output" : "build",
  // project_name is used to prepend header define so it doesn't collide with any of your defines
  "project_name" : "resource_builder"
}
~~~
Don't forget to remove comments if you use this sample (json doesn't support comments).

In your code you can get resource data and size by calling appropriate functions:
~~~
#include "resource_builder/resources.h"

uint8_t* data = ResourceBuilder::get_resource_data(ResourceBuilder::RES_YOUR_RES_NAME);
uint32_t sz = ResourceBuilder::get_resource_size(ResourceBuilder::RES_YOUR_RES_NAME);
~~~

All resource ids are available in enum `ResourceBuilder::ResourceId`

Examples
--------

A fully functional CMake project is available in `example` directory to show how resources are stored and used in code.
In that example a few icons and a text file are embedded into executable. At runtime we access icon data
(only print its size and output text file contains.

Mirrors
-------

The project is stored at:

BitBucket https://bitbucket.org/funbiscuit/resource-builder

Github https://github.com/funbiscuit/resource-builder
