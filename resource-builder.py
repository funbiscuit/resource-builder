#!/usr/bin/python3
import argparse
import fnmatch
import re
import os
import sys
import subprocess
import json
import time
import platform
from shutil import rmtree

parser = argparse.ArgumentParser(description="Arg parser")
parser.add_argument('work_dir')
parser.add_argument('-t', dest='timeout', help='how much to wait for another instance to finish (in seconds)')
# 10s is enough to process hundreds of files (with objcopy/ld), change if you need more time
parser.set_defaults(timeout=10)
args = parser.parse_args()
timeout = float(args.timeout)

if not os.path.exists(args.work_dir):
    print("Working directory %s does not exist!" % args.work_dir)
    sys.exit(-1)

os.chdir(args.work_dir)

try:
    lock_file = open("resource-builder.lock", "x")
    lock_file.close()
except FileExistsError as e:
    start = time.time()
    # if lock file exist, there are two options: another instance is running or it has crashed
    # if this is the first option - just wait until another instance finishes its job and
    # report that files were created by it (not treated as error)
    # if in `timeout` seconds another instance doesn't finish - there is a good chance it has crashed
    # and leaved its lock file in place. Report this as error and tell user to manually delete lock file
    # Usually runtime of this script is less than a second.
    # But even with objcopy/ld and hundreds of files it runs in less than 10 seconds
    print("Waiting up to %0.2f seconds for another instance to finish..." % timeout)
    while os.path.isfile("resource-builder.lock") and time.time() < start+timeout:
        time.sleep(0.1)
    if os.path.isfile("resource-builder.lock"):
        print("Another instance did not finish in specified amount of time, exiting.\n" +
              "If you are sure, this is not true, manually delete " +
              "lock file resource-builder.lock from resources directory.")
        print("If you are sure that you need more time for resource generation send it as argument:")
        print("python resource-builder.py -t=[timeout in seconds] [work_dir]")
        sys.exit(-1)
    else:
        print("Files were created by another instance, exiting.\n" +
              "If you are sure, this is not true, restart script.")
        sys.exit(0)

if not os.path.exists("resources.json"):
    print("Working directory %s should contain resources.json!" % args.work_dir)
    sys.exit(-1)

cmakeTemplate = """# THIS IS AUTOGENERATED CMAKE FILE, DO NOT MODIFY
cmake_minimum_required(VERSION 3.1)

set(RES_BUILDER_NAME %s)

project(${RES_BUILDER_NAME} VERSION 1.0 LANGUAGES CXX)

add_library(${RES_BUILDER_NAME} STATIC src/resources.cpp)
target_compile_features(${RES_BUILDER_NAME} PUBLIC cxx_std_11)
target_include_directories(${RES_BUILDER_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
if(UNIX AND NOT WIN32)
    target_compile_options(${RES_BUILDER_NAME} PRIVATE -fPIC)
endif()
%s
add_library(${RES_BUILDER_NAME}::${RES_BUILDER_NAME} ALIAS ${RES_BUILDER_NAME})
"""
cmakeWinTemplate = """
# On windows resources are compiled with source by using .rc file
target_sources(${RES_BUILDER_NAME} INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/src/win.rc)
"""
cmakeNixTemplate = """
# On linux and macos object files are created and should be linked with resources library
target_link_libraries(${RES_BUILDER_NAME} PRIVATE
%s        )
"""
headerTemplate = """/**
 * THIS IS AUTOGENERATED HEADER, DO NOT MODIFY
 */

#ifndef %s_RESOURCE_BUILDER_H
#define %s_RESOURCE_BUILDER_H
#include <cstdint>
#include <string>

namespace ResourceBuilder {
    enum class ResId {
        %s
    };

    /**
     * Wraps utf-8 text into string.
     * Internally calls get_resource_data and get_resource_size.
     * Allocates temporary char array with extra char for null-byte since embedded resource
     * might not have null byte at the end.
     * @param id - resource id
     * @return string encapsulating resource text
     */
    std::string get_resource_text(ResId id);

    /**
     * Returns resource data for given ID. Do not attempt to delete it!
     * Call get_resource_size to get size of array
     * @param id - resource id
     * @return pointer to data
     */
    const uint8_t * get_resource_data(ResId id);

    /**
     * Returns size of resource data for given ID.
     * Do not attempt to access memory outside. This will lead to undefined behavior.
     * @param id - resource id
     * @return data size
     */
    uint32_t get_resource_size(ResId id);
}
#endif //%s_RESOURCE_BUILDER_H
"""
sourceTemplate = """/**
 * THIS IS AUTOGENERATED FILE, DO NOT MODIFY
 */

#include "resource_builder/resources.h"
#include <memory>
#include <cstring>

std::string ResourceBuilder::get_resource_text(ResourceBuilder::ResId id)
{
    auto data = ResourceBuilder::get_resource_data(id);
    auto sz = ResourceBuilder::get_resource_size(id);
    if(!data || sz == 0 )
        return "";
    // This is important when embedding string data. It is not guaranteed that we can read byte after
    // last character and if it is even '\0'. So we need to copy data and set null byte manually
    auto cstr = std::unique_ptr<char[]>(new char[sz+1]);
    memcpy(cstr.get(), data, sz);
    cstr[sz] = '\\0';

    // unique_ptr will delete allocated array for us
    return std::string(cstr.get());
}

#ifdef __linux__

%s
const uint8_t* ResourceBuilder::get_resource_data(ResourceBuilder::ResId id) {
    uint8_t* starts[] = {%s};
    return starts[static_cast<int>(id)];
}

uint32_t ResourceBuilder::get_resource_size(ResourceBuilder::ResId id) {
    uint32_t sizes[] = {%s};
    return sizes[static_cast<int>(id)];
}
#endif

#ifdef _WIN32

#include <Windows.h>
#include <WinUser.h>

const uint8_t* ResourceBuilder::get_resource_data(ResourceBuilder::ResId id) {
    static bool is_loaded = false;
    static const char* names[] = {%s};
    static uint8_t* starts[%d];
    
    if(!is_loaded) {
        is_loaded = true;
        
        for(int i = 0; i<%d; ++i) {
            auto info = FindResourceA(nullptr, names[i], RT_RCDATA);
            starts[i] = static_cast<uint8_t*>(LoadResource(nullptr, info));
        }
    }

    return starts[static_cast<int>(id)];
}

uint32_t ResourceBuilder::get_resource_size(ResourceBuilder::ResId id) {
    static bool is_loaded = false;
    static const char* names[] = {%s};
    static uint32_t sizes[%d];
    
    if(!is_loaded) {
        is_loaded = true;
        
        for(int i = 0; i<%d; ++i) {
            auto info = FindResourceA(nullptr, names[i], RT_RCDATA);
            sizes[i] = static_cast<uint32_t>(SizeofResource(nullptr, info));
        }
    }
    
    return sizes[static_cast<int>(id)];
}
#endif

#if __APPLE__
#include <cstdio>
#include <mach-o/getsect.h>
#include <mach-o/ldsyms.h>

const uint8_t* ResourceBuilder::get_resource_data(ResourceBuilder::ResId id) {
    static bool is_loaded = false;
    static uint8_t* starts[%d];
    
    if(!is_loaded) {
        is_loaded = true;
        //17 would be enough since section name is only 16 bytes long
        char buf[20];
        
        for(int i = 0; i<%d; ++i) {
            sprintf(buf, "_res_sec_%%d", i);
            size_t sz;
            starts[i] = static_cast<uint8_t*>(getsectiondata(&_mh_execute_header, "binary", buf, &sz));
        }
    }

    return starts[static_cast<int>(id)];
}

uint32_t ResourceBuilder::get_resource_size(ResourceBuilder::ResId id) {
    static bool is_loaded = false;
    static uint32_t sizes[%d];
    
    if(!is_loaded) {
        is_loaded = true;
        //17 would be enough since section name is only 16 bytes long
        char buf[20];
        
        for(int i = 0; i<%d; ++i) {
            sprintf(buf, "_res_sec_%%d", i);
            size_t sz;
            getsectiondata(&_mh_execute_header, "binary", buf, &sz);
            sizes[i] = sz;
        }
    }
    
    return sizes[static_cast<int>(id)];
}

#endif
"""


def is_resource(filename):
    r = False
    for res in resources:
        if fnmatch.fnmatch(filename, res):
            r = True
            break
    return r


def get_var_name(file):
    return re.sub(r'[^A-Za-z0-9]', '_', file)


def process_resource(file):
    print("Including resource %s" % file)

    name = get_var_name(file)
    varNames.append((name, file))


varNames = []

with open("resources.json") as data_file:
    config = json.load(data_file)
    resources = config["resources"]
    output = config["output"]
    project_name = config["project_name"]

    if not os.path.exists(output):
        os.mkdir(output)
    if not os.path.exists(output + "/objs"):
        os.mkdir(output + "/objs")
    if not os.path.exists(output + "/include"):
        os.mkdir(output + "/include")
    if not os.path.exists(output + "/src"):
        os.mkdir(output + "/src")
    if not os.path.exists(output + "/temp"):
        os.mkdir(output + "/temp")
    if not os.path.exists(output + "/include/resource_builder"):
        os.mkdir(output + "/include/resource_builder")

    print("Scan resource files")
    for dirName, subdirList, fileList in os.walk("."):
        for f in fileList:
            local_file = dirName + "/" + f
            if f != "resource-builder.lock" and is_resource(local_file):
                process_resource(local_file)

    created_objs = []

    print("Creating platform specific files")
    if sys.platform == "win32":
        with open("./build/src/win.rc", "w") as winFile:
            for var in varNames:
                path = var[1].replace("\\", "/")
                winFile.write("%s RCDATA \"./../../%s\"\n" % (var[0], path))
            winFile.close()
    elif sys.platform.startswith('linux'):
        arch = platform.machine()
        if arch == 'x86_64':
            o_flag, b_flag = "elf64-x86-64", "i386:x86-64"
        elif arch in ('i686', 'i386'):
            o_flag, b_flag = "elf32-i386", "i386"
        elif arch == 'armv7l':
            o_flag, b_flag = "elf32-littlearm", "arm"
        elif arch == 'aarch64':
            o_flag, b_flag = "elf64-aarch64", "aarch64"
        elif arch == 'ppc':
            o_flag, b_flag = "elf32-powerpc", "powerpc"
        elif arch == 'ppc64':
            o_flag, b_flag = "elf64-powerpc", "powerpc:common64"
        elif arch == 'mips':
            o_flag, b_flag = "elf32-tradbigmips", "mips"
        elif arch == 'mipsel':
            o_flag, b_flag = "elf32-tradlittlemips", "mipsel"
        elif arch == 'mips64':
            o_flag, b_flag = "elf64-tradbigmips", "mips64"
        elif arch == 'mips64el':
            o_flag, b_flag = "elf64-tradlittlemips", "mips64el"
        elif arch == 'riscv32':
            o_flag, b_flag = "elf32-littleriscv", "riscv:rv32"
        elif arch == 'riscv64':
            o_flag, b_flag = "elf64-littleriscv", "riscv:rv64"
        else:
            raise ValueError("Unsupported architecture: %s" % arch)
        for var in varNames:
            out_file = "%s/objs/%s.o" % (output, var[0])
            created_objs.append("%s.o" % var[0])
            subprocess.call(["objcopy", "-I", "binary", "-O", o_flag, "-B", b_flag, var[1], out_file])
    elif sys.platform.startswith('darwin'):
        # use approach from https://stackoverflow.com/a/13772389/7694893
        stub_src = "./build/temp/stub.c"
        stub_obj = "./build/temp/stub.o"
        open(stub_src, "w").close()
        subprocess.call(["gcc", "-o", stub_obj, "-c", stub_src])
        counter = 0
        for var in varNames:
            # section name is limited to 16 symbols, so up to 10,000,000 resources can be embedded (count from 0)
            mac_sect = "_res_sec_%d" % counter
            out_file = "%s/objs/%s.o" % (output, var[0])
            created_objs.append("%s.o" % var[0])
            subprocess.call(["ld", "-r", "-o", out_file, "-sectcreate", "binary", mac_sect, var[1], stub_obj])
            counter += 1

    print("Clean up unused platform files")
    # delete old objects that were not created now (subdirs too)
    for dirName, subdirList, fileList in os.walk("%s/objs" % output):
        # remove files that were not generated in this run
        for f in fileList:
            delete_file = True
            for obj in created_objs:
                if obj == f:
                    delete_file = False
                    break
            if delete_file:
                os.remove("%s/objs/%s" % (output, f))
        # remove all dirs (we are not generating them)
        for d in subdirList:
            rmtree("%s/objs/%s" % (output, d))
        break

    with open("./build/CMakeLists.txt", "w") as cmakeLists:
        if sys.platform == "win32":
            cmakeLists.write(cmakeTemplate % (project_name, cmakeWinTemplate))
        else:
            objsString = "";
            # include all created objs
            for obj in created_objs:
                objsString += "        ${CMAKE_CURRENT_SOURCE_DIR}/objs/%s\n" % obj
            cmakeLists.write(cmakeTemplate % (project_name, (cmakeNixTemplate % objsString)))
        cmakeLists.close()

    with open("./build/include/resource_builder/resources.h", "w") as header:
        ids = ""
        isFirst = True
        counter = 0
        for var in varNames:
            if not isFirst:
                # for second and other ids add comma, new line and 8 spaces
                ids += ",\n        "
            ids += "%s = %d" % (var[0].upper(), counter)
            counter += 1
            isFirst = False
        header_def = project_name.upper()
        header.write(headerTemplate % (header_def, header_def, ids, header_def))
        header.close()

    with open("./build/src/resources.cpp", "w") as source:
        extern_vars = ""
        starts_arr = ""
        sizes_arr = ""
        names_arr = ""
        counter = 0
        isFirst = True
        for var in varNames:
            counter += 1
            start = "_binary_" + var[0] + "_start"
            end = "_binary_" + var[0] + "_end"
            if not isFirst:
                # spaces are for proper indentation
                starts_arr += ",\n                         "
                sizes_arr += ",\n                        "
                names_arr += ",\n                                  "
            isFirst = False

            extern_vars += "extern uint8_t " + start + ";\n"
            extern_vars += "extern uint8_t " + end + ";\n"
            starts_arr += "&" + start
            names_arr += "\"" + var[0] + "\""
            sizes_arr += "static_cast<uint32_t>(&" + end + " - &" + start + ")"

        source.write(sourceTemplate % (extern_vars, starts_arr, sizes_arr,
                                       names_arr, counter, counter, names_arr, counter, counter,
                                       counter, counter, counter, counter))
        source.close()

        print("%d resources were successfully processed." % counter)

os.remove("resource-builder.lock")
