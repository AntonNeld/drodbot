MODULE_SUFFIX=$(shell python3.8-config --extension-suffix)
PYBIND11_INCLUDES=$(shell python3 -m pybind11 --includes)
INCLUDES=$(PYBIND11_INCLUDES) -I/usr/include/python3.8 -Idrod -Imetakit/include -I/usr/include/jsoncpp
# -Wno-parentheses is to suppress a warning from metakit
WARNING_ARGS=-Wall -Werror -Wno-parentheses
COMMON_COMPILE_ARGS=-O3 -std=c++11 -fPIC $(INCLUDES) $(shell sdl2-config --cflags)

DRODLIB_FILES=$(shell find drod/DRODLib -name '*.cpp')
DRODLIB_OBJECT_FILES=$(patsubst drod/DRODLib/%.cpp,build/DRODLib/%.o,$(DRODLIB_FILES))

all: temp_module_name$(MODULE_SUFFIX)

temp_module_name$(MODULE_SUFFIX):temp.o $(DRODLIB_OBJECT_FILES)
	g++ -shared -o temp_module_name$(MODULE_SUFFIX) build/temp.o -lpython3.8

temp.o: temp.cpp build
	g++ -c $(WARNING_ARGS) $(COMMON_COMPILE_ARGS) temp.cpp -o build/temp.o

# We don't include warnings when compiling DROD code since
# we're not going to change it anyway
build/DRODLib/%.o: drod/DRODLib/%.cpp build
	g++ -c $(COMMON_COMPILE_ARGS) $< -o $@

build:
	mkdir build
	mkdir build/DRODLib

clean:
	rm -rf build
	rm -f temp_module_name$(MODULE_SUFFIX)