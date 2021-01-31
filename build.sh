#!/usr/bin/env bash

# Run this to compile the C++ parts, like DRODLib.
# It may be replaced by something more standard later.
g++ -O3 -Wall -Werror -shared -std=c++11 -fPIC `python3 -m pybind11 --includes` \
-Isrc/drod_lib/drod -Isrc/drod_lib/metakit/include \
src/drod_lib/temp.cpp -o src/drod_lib/temp_module_name`python3.8-config --extension-suffix`