#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "typedefs.h"
#include "RoomPlayer.h"
#include "Room.h"

RoomPlayer roomPlayer = RoomPlayer();

void initialize()
{
    roomPlayer.initialize();
}

Room simulateAction(Room room, Action action)
{
    roomPlayer.setRoom(room);
    roomPlayer.performAction(action);
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

Parameters
----------
room
    The room before taking the action.
action
    The action to take, as an integer. The integer for each action is the value
    of the action in the Action enum in common.py.

Returns
-------
The room after the action.
)docstr",
          pybind11::arg("room"), pybind11::arg("action"));

    pybind11::enum_<Action>(m, "Action")
        .value("SW", Action::SW)
        .value("S", Action::S)
        .value("SE", Action::SE)
        .value("W", Action::W)
        .value("WAIT", Action::WAIT)
        .value("E", Action::E)
        .value("NW", Action::NW)
        .value("N", Action::N)
        .value("NE", Action::NE)
        .value("CW", Action::CW)
        .value("CCW", Action::CCW)
        .export_values();

    pybind11::enum_<ElementType>(m, "ElementType")
        .value("UNKNOWN", ElementType::UNKNOWN)
        .value("NOTHING", ElementType::NOTHING)
        .value("WALL", ElementType::WALL)
        .value("PIT", ElementType::PIT)
        .value("MASTER_WALL", ElementType::MASTER_WALL)
        .value("YELLOW_DOOR", ElementType::YELLOW_DOOR)
        .value("YELLOW_DOOR_OPEN", ElementType::YELLOW_DOOR_OPEN)
        .value("GREEN_DOOR", ElementType::GREEN_DOOR)
        .value("GREEN_DOOR_OPEN", ElementType::GREEN_DOOR_OPEN)
        .value("BLUE_DOOR", ElementType::BLUE_DOOR)
        .value("BLUE_DOOR_OPEN", ElementType::BLUE_DOOR_OPEN)
        .value("STAIRS", ElementType::STAIRS)
        .value("FORCE_ARROW", ElementType::FORCE_ARROW)
        .value("CHECKPOINT", ElementType::CHECKPOINT)
        .value("ORB", ElementType::ORB)
        .value("SCROLL", ElementType::SCROLL)
        .value("OBSTACLE", ElementType::OBSTACLE)
        .value("BEETHRO", ElementType::BEETHRO)
        .value("BEETHRO_SWORD", ElementType::BEETHRO_SWORD)
        .value("ROACH", ElementType::ROACH)
        .value("CONQUER_TOKEN", ElementType::CONQUER_TOKEN)
        .value("FLOOR", ElementType::FLOOR)
        .export_values();

    pybind11::enum_<Direction>(m, "Direction")
        .value("NONE", Direction::NONE)
        .value("N", Direction::N)
        .value("NE", Direction::NE)
        .value("E", Direction::E)
        .value("SE", Direction::SE)
        .value("S", Direction::S)
        .value("SW", Direction::SW)
        .value("W", Direction::W)
        .value("NW", Direction::NW)
        .export_values();

    pybind11::enum_<OrbEffect>(m, "OrbEffect")
        .value("OPEN", OrbEffect::OPEN)
        .value("CLOSE", OrbEffect::CLOSE)
        .value("TOGGLE", OrbEffect::TOGGLE)
        .export_values();

    pybind11::class_<Element>(m, "Element")
        .def(pybind11::init<ElementType, Direction, OrbEffects>(),
             pybind11::arg("element_type") = ElementType::NOTHING,
             pybind11::arg("direction") = Direction::NONE,
             pybind11::arg("orb_effects") = OrbEffects())
        .def_readwrite("element_type", &Element::type)
        .def_readwrite("direction", &Element::direction)
        .def_readwrite("orb_effects", &Element::orbEffects);

    pybind11::class_<Tile>(m, "Tile")
        .def(pybind11::init<Element, Element, Element, Element, Element>(),
             pybind11::arg_v("room_piece", Element(), "Element()"),
             pybind11::arg_v("floor_control", Element(), "Element()"),
             pybind11::arg_v("checkpoint", Element(), "Element()"),
             pybind11::arg_v("item", Element(), "Element()"),
             pybind11::arg_v("monster", Element(), "Element()"))
        .def_readwrite("room_piece", &Tile::roomPiece)
        .def_readwrite("floor_control", &Tile::floorControl)
        .def_readwrite("checkpoint", &Tile::checkpoint)
        .def_readwrite("item", &Tile::item)
        .def_readwrite("monster", &Tile::monster);

    pybind11::class_<Room>(m, "Room")
        .def(pybind11::init<Tiles>(), pybind11::arg("tiles"))
        .def("copy", &Room::copy, R"docstr(
Copy the room.

Returns
-------
A copy of the room.
)docstr")
        .def("get_tile", &Room::getTile, pybind11::arg("position"), R"docstr(
Return the tile at the given position.

Parameters
----------
position
    A tuple (x, y).

Returns
-------
The tile at that position.
)docstr")
        .def("set_tile", &Room::setTile, pybind11::arg("position"), pybind11::arg("tile"), R"docstr(
Set the tile at the given position.

Parameters
----------
position
    A tuple (x, y).
tile
    The tile to set. 
)docstr");
}