#!/usr/bin/env bash

# Run this to compile the C++ parts, like DRODLib.

cd src/room_simulator
if [ ! -d build ]; then
    pipenv run make clean
fi
pipenv run make
PYTHONPATH=../ pipenv run pybind11-stubgen room_simulator
mv stubs/room_simulator-stubs/__init__.pyi ../room_simulator.pyi
rm -r stubs