#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "typedefs.h"
#include "RoomPlayer.h"

RoomPlayer roomPlayer = RoomPlayer();

void initialize()
{
    roomPlayer.initialize();
}

int simulateAction(int roomType, int action)
{
    roomPlayer.setRoom(roomType);
    roomPlayer.performAction(static_cast<Action>(action));
    return roomPlayer.getRoom();
}

PYBIND11_MODULE(room_simulator, m)
{
    m.doc() = "This module uses the DROD code to simulate actions in rooms.";
    m.def("initialize", &initialize, R"docstr(
Initialize the room simulator.

This has side effects on the file system and should only be done once.
)docstr");
    m.def("simulate_action", &simulateAction, R"docstr(
Simulate an action in a room.

Currently only simulates one of three predefined rooms.

Parameters
----------
room_type
    The predefined room to use. 0, 1 or other.
action
    The action to take, as an integer. The integer for each action is the value
    of the action in the Action enum in common.py.

Returns
-------
The X coordinate of Beethro after the move.
)docstr",
          pybind11::arg("room_type"), pybind11::arg("action"));
}