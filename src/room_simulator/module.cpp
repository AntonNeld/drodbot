#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "typedefs.h"
#include "RoomPlayer.h"
#include "Room.h"
#include "search/AStarSearcher.h"
#include "problems/PathfindingProblem.h"
#include "problems/RoomProblem.h"

void initialize()
{
    initGlobalRoomPlayer();
}

Room simulateAction(Room room, Action action)
{
    globalRoomPlayer.setRoom(room);
    globalRoomPlayer.performAction(action);
    return globalRoomPlayer.getRoom();
}

template <class State, class SearchAction>
void addAStarSearcher(pybind11::module_ &m, const char *name, const char *problemName)
{
    // Also add a base Problem of the correct type
    pybind11::class_<Problem<State, SearchAction>>(m, problemName);

    pybind11::class_<AStarSearcher<State, SearchAction>>(m, name, R"docstr(
This performs A* search in an inspectable way.

Parameters
----------
problem
    The problem to solve.
)docstr")
        .def(pybind11::init<Problem<State, SearchAction> *>(),
             pybind11::arg("problem"))
        .def("find_solution", &AStarSearcher<State, SearchAction>::findSolution, R"docstr(
Find a solution to the problem.

This is all you need when using this for real.

Returns
-------
A list of actions solving the problem.
)docstr")
        .def("expand_next_node", &AStarSearcher<State, SearchAction>::expandNextNode, R"docstr(
Expand the next node in the search.
)docstr")
        .def("get_iterations", &AStarSearcher<State, SearchAction>::getIterations, R"docstr(
Get the number of iterations.

Returns
-------
The number of iterations.
)docstr")
        .def("get_current_path", &AStarSearcher<State, SearchAction>::getCurrentPath, R"docstr(
Get the path to the current node.

Returns
-------
The actions resulting in the current node.
)docstr")
        .def("get_current_state", &AStarSearcher<State, SearchAction>::getCurrentState, R"docstr(
Get the state of the current node.

Returns
-------
The state of the current node.
)docstr")
        .def("get_current_state_heuristic", &AStarSearcher<State, SearchAction>::getCurrentStateHeuristic, R"docstr(
Get the heuristic function value of the state of the current node.

Returns
-------
The heuristic function value of the state of the current node.
)docstr")
        .def("get_frontier_states", &AStarSearcher<State, SearchAction>::getFrontierStates, R"docstr(
Get the states in the frontier.

Returns
-------
The states in the frontier.
)docstr")
        .def("get_explored", &AStarSearcher<State, SearchAction>::getExplored, R"docstr(
Get the explored states.

Returns
-------
The explored states.
)docstr")
        .def("found_solution", &AStarSearcher<State, SearchAction>::foundSolution, R"docstr(
Whether we have found the solution.

Returns
-------
Whether we have found the solution.
)docstr");
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
    The action to take.

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
)docstr")
        .def("find_coordinates", &Room::findCoordinates, pybind11::arg("element_type"), R"docstr(
Find the coordinates of all elements of a type.

Parameters
----------
element_type
    The element type to find the coordinates of.

Returns
-------
The coordinates of all elements of that type, as a list of (x, y) tuples.
)docstr")
        .def("find_player", &Room::findPlayer, R"docstr(
Find the coordinates of the player.

Returns
-------
A tuple ((x, y), direction).
)docstr")
        .def("is_passable", &Room::isPassable, pybind11::arg("x"), pybind11::arg("y"), R"docstr(
Check whether a tile is passable.

It currently does not take into account force arrows, or
whether doors can be opened.

Parameters
----------
x
    The x coordinate.
y
    The y coordinate.

Returns
-------
Whether the tile is passable or not.
)docstr");

    pybind11::class_<Objective>(m, "Objective")
        .def(pybind11::init<bool, std::set<Position>>(), pybind11::arg("sword_at_tile"), pybind11::arg("tiles"))
        .def_readwrite("sword_at_tile", &Objective::swordAtTile)
        .def_readwrite("tiles", &Objective::tiles);

    addAStarSearcher<Position, Action>(m, "AStarSearcherPositionAction", "ProblemPositionAction");
    addAStarSearcher<Room, Action>(m, "AStarSearcherRoomAction", "ProblemRoomAction");

    pybind11::class_<PathfindingProblem, Problem<Position, Action>>(m, "PathfindingProblem", R"docstr(
A problem for finding a path in a room.

Parameters
----------
start_position
    The starting position in the room.
room
    The room.
goals
    The goal positions.
use_heuristic
    Whether to use a heuristic function. The heuristic is the shortest distance
    to the nearest goal, disregarding obstacles.
)docstr")
        .def(pybind11::init<Position, Room, std::set<Position>, bool>(),
             pybind11::arg("start_position"),
             pybind11::arg("room"),
             pybind11::arg("goals"),
             pybind11::arg("use_heuristic") = true);
    pybind11::class_<RoomProblem, Problem<Room, Action>>(m, "RoomProblem", R"docstr(
A problem for reaching an objective in a room.

Parameters
----------
room
    The room.
objective
    The objective.
)docstr")
        .def(pybind11::init<Room, Objective>(),
             pybind11::arg("room"),
             pybind11::arg("objective"));
}