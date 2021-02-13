// This file is just to play around to try to get C++ bindings working at all.
// It will be removed later.

#include <iostream>
#include <pybind11/pybind11.h>

#include "RoomPlayer.h"

RoomPlayer roomPlayer = RoomPlayer();

void initialize()
{
    roomPlayer.initialize();
}

int simulateMove(int roomType)
{
    roomPlayer.setRoom(roomType);
    roomPlayer.performAction();
    return roomPlayer.getRoom();
}

PYBIND11_MODULE(room_simulator, m)
{
    m.doc() = "This module uses the DROD code to simulate moves in rooms.";
    m.def("initialize", &initialize, R"docstr(
Initialize the room simulator.

This has side effects on the file system and should only be done once.
)docstr");
    m.def("simulate_move", &simulateMove, R"docstr(
Simulate a move in a room.

Currently only simulates moving SE in one of three predefined rooms.

Parameters
----------
roomType
    The predefined room to use. 0, 1 or other.

Returns
-------
The X coordinate of Beethro after the move.
)docstr");
}