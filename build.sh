#!/usr/bin/env bash

# Run this to compile the C++ parts, like DRODLib.

cd src/drod_lib
if [ ! -d build ]; then
    pipenv run make clean
fi
pipenv run make
