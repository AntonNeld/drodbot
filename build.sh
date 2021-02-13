#!/usr/bin/env bash

# Run this to compile the C++ parts, like DRODLib.

cd src/room_simulator
if [ ! -d build ]; then
    pipenv run make clean
fi
pipenv run make
