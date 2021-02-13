MODULE_SUFFIX=$(shell python3.8-config --extension-suffix)
PYBIND11_INCLUDES=$(shell python3 -m pybind11 --includes)
INCLUDES=$(PYBIND11_INCLUDES) -I/usr/include/python3.8 -Idrod -Imetakit/include -I/usr/include/jsoncpp
# -Wno-parentheses is to suppress a warning from metakit
WARNING_ARGS=-Wall -Werror -Wno-parentheses
COMMON_COMPILE_ARGS=-O3 -std=c++11 -fPIC $(INCLUDES) $(shell sdl2-config --cflags)

BACKENDLIB_FILES=$(shell find drod/BackEndLib -name '*.cpp')
BACKENDLIB_OBJECT_FILES=$(patsubst drod/BackEndLib/%.cpp,build/BackEndLib/%.o,$(BACKENDLIB_FILES))
DRODLIB_FILES=$(shell find drod/DRODLib -name '*.cpp')
DRODLIB_OBJECT_FILES=$(patsubst drod/DRODLib/%.cpp,build/DRODLib/%.o,$(DRODLIB_FILES))
METAKIT_FILES=$(shell find metakit/src -name '*.cpp')
METAKIT_OBJECT_FILES=$(patsubst metakit/src/%.cpp,build/metakit/%.o,$(METAKIT_FILES))
OWN_FILES=$(shell find . -maxdepth 1 -name '*.cpp')
OWN_OBJECT_FILES=$(patsubst %.cpp,build/own/%.o,$(OWN_FILES))
OBJECT_FILES=$(BACKENDLIB_OBJECT_FILES) $(DRODLIB_OBJECT_FILES) $(METAKIT_OBJECT_FILES) $(OWN_OBJECT_FILES)

LINK_LIBS=$(shell sdl2-config --libs) -lpython3.8 -ljsoncpp -lcurl

temp_module_name$(MODULE_SUFFIX): $(OBJECT_FILES)
	g++ -shared -o temp_module_name$(MODULE_SUFFIX) $(OBJECT_FILES) $(LINK_LIBS)

build/own/%.o: %.cpp
	g++ -c $(WARNING_ARGS) $(COMMON_COMPILE_ARGS) $< -o $@

# We don't include warnings when compiling source from other projects,
# since we won't change it anyway
build/DRODLib/%.o: drod/DRODLib/%.cpp
	g++ -c $(COMMON_COMPILE_ARGS) $< -o $@

build/BackEndLib/%.o: drod/BackEndLib/%.cpp
	g++ -c $(COMMON_COMPILE_ARGS) $< -o $@

# Even though this is a pattern rule, it will only be run once
build/metakit/%.o: metakit/src/%.cpp
	cd metakit/builds && ../unix/configure && make
	mv metakit/builds/*.o build/metakit/
	find metakit/builds/ ! -name '!keepme.txt' -type f -exec rm -f {} +

clean:
	rm -rf build
	rm -f temp_module_name$(MODULE_SUFFIX)
	# Init directory structure again
	mkdir build
	mkdir build/DRODLib
	mkdir build/BackEndLib
	mkdir build/metakit
	mkdir build/DRODLibTests