[![Build status](https://ci.appveyor.com/api/projects/status/awfkahvjccosn8il/branch/master?svg=true)](https://ci.appveyor.com/project/funbiscuit/resource-builder/branch/master)

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

Suppose in CMakeLists.txt you create your executable:
~~~
add_executable(YourExecutableName)
~~~

In CMakeLists.txt add following code:

~~~
find_package( PythonInterp 3.0 REQUIRED )

#if you put your resource files not in ./res folder make changes here
execute_process(COMMAND ${PYTHON_EXECUTABLE}
        ${PROJECT_SOURCE_DIR}/libs/resource-builder/resource-builder.py #path to python script that builds resources
        ${PROJECT_SOURCE_DIR}/res                                       #work directory where resources are stored
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

#resource will be compiled in res/build folder (it is specified in res/resources.json)
#only need to add it as subdirectory and link to created library
add_subdirectory(res/build)
target_link_libraries(YourExecutableName PRIVATE ResourceBuilder::ResourceBuilder)
~~~

This runs python script to generate all required files and then you just
write two lines to include everything in your project.

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
  // it is also used to name static library that you'll need to link your executable
  "project_name" : "ResourceBuilder"
}
~~~
Don't forget to remove comments if you use this sample (json doesn't support comments).

In your code you can get resource data and size (or text) by calling appropriate functions:
~~~
#include "resource_builder/resources.h"

// ...

uint8_t* data = ResourceBuilder::get_resource_data(ResourceBuilder::ResId::YOUR_RES_NAME);
uint32_t sz = ResourceBuilder::get_resource_size(ResourceBuilder::ResId::YOUR_RES_NAME);
std::string utf8text = ResourceBuilder::get_resource_text(ResourceBuilder::ResId::YOUR_RES_NAME);
~~~

All resource ids are available in enum class `ResourceBuilder::ResId`

Examples
--------

A fully functional CMake project is available in `example` directory to show how resources are stored and used in code.
In that example a few icons and a text file are embedded into executable. At runtime we access icon data
(only print its size in bytes) and output text file contains.

Mirrors
-------

The project is stored at:

BitBucket https://bitbucket.org/funbiscuit/resource-builder

Github https://github.com/funbiscuit/resource-builder

License
-------

The project is licensed under MIT license (look LICENSE.txt)
