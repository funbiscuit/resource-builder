Resource Builder for C++
------------------------

A simple cross-platform resource builder for C++ programs.
Works on Linux and Windows.

On Linux uses `objcopy` to generate
object files that will link with your code.

On Windows `.rc` file is generated to be compiled with your code.


Example usage
-------------
It is the simplest to use this builder with CMake project.
In CMakeLists.txt add following code:

~~~
find_package( PythonInterp 3.0 REQUIRED )

#if you put your resource files not in ./res folder make changes here
add_custom_target(
        resource_builder ALL
        COMMAND ${PYTHON_EXECUTABLE} ${PROJECT_SOURCE_DIR}/libs/resource-builder/resource-builde.py ${PROJECT_SOURCE_DIR}/res
        BYPRODUCTS ${PROJECT_SOURCE_DIR}/res/build/include/resources.h ${PROJECT_SOURCE_DIR}/res/build/src/resources.cpp
        COMMENT "Building resources"
)

#your add_executable should be called before add_depenndencies is called

#replace ${PROJECT_NAME} with name of executable if needed
add_dependencies(${PROJECT_NAME} resource_builder)
~~~

Place `resources.json` inside `res` directory in your project root.
