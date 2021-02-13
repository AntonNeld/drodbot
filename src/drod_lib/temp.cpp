// This file is just to play around to try to get C++ bindings working at all.
// It will be removed later.

#include <iostream>
#include <pybind11/pybind11.h>

#include "RoomPlayer.h"

int temp()
{
    RoomPlayer roomPlayer = RoomPlayer();
    roomPlayer.initialize();
    std::cout << "==Room 0==" << std::endl;
    roomPlayer.setRoom(0);
    std::cout << "X before: " << roomPlayer.getRoom() << std::endl;
    roomPlayer.performAction();
    std::cout << "X after: " << roomPlayer.getRoom() << std::endl;

    std::cout << "==Room 1==" << std::endl;
    roomPlayer.setRoom(1);
    std::cout << "X before: " << roomPlayer.getRoom() << std::endl;
    roomPlayer.performAction();
    std::cout << "X after: " << roomPlayer.getRoom() << std::endl;
    return 0;
}

PYBIND11_MODULE(temp_module_name, m)
{
    m.doc() = "Just a module.";
    m.def("hello_world", &temp, "Do something in some rooms");
}