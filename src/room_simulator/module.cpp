#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "typedefs.h"
#include "RoomPlayer.h"
#include "Room.h"
#include "DerivedRoom.h"
#include "ObjectiveReacher.h"
#include "search/Searcher.h"
#include "problems/PathfindingProblem.h"
#include "problems/PlanningProblem.h"
#include "problems/DerivedRoomProblem.h"
#include "utils.h"

void initialize()
{
    initRoomPlayerRequirements();
}

Room simulateActions(Room room, std::vector<Action> actions)
{
    RoomPlayer roomPlayer = RoomPlayer(room);
    roomPlayer.setActions(actions);
    Room resultingRoom = roomPlayer.getRoom();
    return resultingRoom;
}

template <class State, class SearchAction>
void addSearcher(pybind11::module_ &m, const char *name, const char *problemName, const char *solutionName)
{
    // Also add a base Problem of the correct type
    pybind11::class_<Problem<State, SearchAction>>(m, problemName);

    // Also add a Solution of the correct type
    pybind11::class_<Solution<State, SearchAction>>(m, solutionName)
        .def(pybind11::init<bool, std::vector<SearchAction>, State, FailureReason>(),
             pybind11::arg("exists"),
             pybind11::arg("actions"),
             pybind11::arg("final_state"),
             pybind11::arg("failure_reason"))
        .def_readwrite("exists", &Solution<State, SearchAction>::exists)
        .def_readwrite("actions", &Solution<State, SearchAction>::actions)
        .def_readwrite("final_state", &Solution<State, SearchAction>::finalState)
        .def_readwrite("failure_reason", &Solution<State, SearchAction>::failureReason);

    pybind11::class_<Searcher<State, SearchAction>>(m, name, R"docstr(
This performs search in an inspectable way.

Parameters
----------
problem
    The problem to solve.
avoid_duplicates
    Whether to keep track of and avoid duplicates.
heuristic_in_priority
    Whether to include the heuristic when prioritizing nodes to expand.
path_cost_in_priority
    Whether to include the path cost when prioritizing nodes to expand.
iteration_limit
    If searching for more than this number of iteration produces no result, throw
    an exception.
)docstr")
        .def(pybind11::init<Problem<State, SearchAction> *, bool, bool, bool, int>(),
             pybind11::arg("problem"),
             pybind11::arg("avoid_duplicates") = true,
             pybind11::arg("heuristic_in_priority") = true,
             pybind11::arg("path_cost_in_priority") = true,
             pybind11::arg("iteration_limit") = 10000)
        .def("find_solution", &Searcher<State, SearchAction>::findSolution, R"docstr(
Find a solution to the problem.

This is all you need when using this for real.

Returns
-------
A Solution object.
)docstr")
        .def("expand_next_node", &Searcher<State, SearchAction>::expandNextNode, R"docstr(
Expand the next node in the search.
)docstr")
        .def("reset", &Searcher<State, SearchAction>::reset, R"docstr(
Reset the search.

This preserves the problem and settings, but resets the search in progress.
)docstr")
        .def("get_iterations", &Searcher<State, SearchAction>::getIterations, R"docstr(
Get the number of iterations.

Returns
-------
The number of iterations.
)docstr")
        .def("get_current_path", &Searcher<State, SearchAction>::getCurrentPath, R"docstr(
Get the path to the current node.

Returns
-------
The actions resulting in the current node.
)docstr")
        .def("get_current_state", &Searcher<State, SearchAction>::getCurrentState, R"docstr(
Get the state of the current node.

Returns
-------
The state of the current node.
)docstr")
        .def("get_current_state_heuristic", &Searcher<State, SearchAction>::getCurrentStateHeuristic, R"docstr(
Get the heuristic function value of the state of the current node.

Returns
-------
The heuristic function value of the state of the current node.
)docstr")
        .def("get_frontier_states", &Searcher<State, SearchAction>::getFrontierStates, R"docstr(
Get the states in the frontier.

Returns
-------
The states in the frontier.
)docstr")
        .def("get_frontier_actions", &Searcher<State, SearchAction>::getFrontierActions, R"docstr(
Get the actions in the frontier.

Returns
-------
The actions in the frontier.
)docstr")
        .def("get_frontier_size", &Searcher<State, SearchAction>::getFrontierSize, R"docstr(
Get the size of the frontier.

Returns
-------
The size of the frontier.
)docstr")
        .def("get_explored", &Searcher<State, SearchAction>::getExplored, R"docstr(
Get the explored states.

Returns
-------
The explored states.
)docstr")
        .def("get_explored_size", &Searcher<State, SearchAction>::getExploredSize, R"docstr(
Get the explored size.

Returns
-------
The explored size.
)docstr")
        .def("found_solution", &Searcher<State, SearchAction>::foundSolution, R"docstr(
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
    m.def("simulate_actions", &simulateActions, R"docstr(
Simulate a actions in a room.

Parameters
----------
room
    The room before taking the actions.
actions
    The actions to take.

Returns
-------
The room after the actions.
)docstr",
          pybind11::arg("room"), pybind11::arg("actions"));

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
        .value("RED_DOOR", ElementType::RED_DOOR)
        .value("RED_DOOR_OPEN", ElementType::RED_DOOR_OPEN)
        .value("TRAPDOOR", ElementType::TRAPDOOR)
        .value("STAIRS", ElementType::STAIRS)
        .value("FORCE_ARROW", ElementType::FORCE_ARROW)
        .value("CHECKPOINT", ElementType::CHECKPOINT)
        .value("ORB", ElementType::ORB)
        .value("MIMIC_POTION", ElementType::MIMIC_POTION)
        .value("INVISIBILITY_POTION", ElementType::INVISIBILITY_POTION)
        .value("SCROLL", ElementType::SCROLL)
        .value("OBSTACLE", ElementType::OBSTACLE)
        .value("BEETHRO", ElementType::BEETHRO)
        .value("BEETHRO_SWORD", ElementType::BEETHRO_SWORD)
        .value("ROACH", ElementType::ROACH)
        .value("ROACH_QUEEN", ElementType::ROACH_QUEEN)
        .value("ROACH_EGG", ElementType::ROACH_EGG)
        .value("EVIL_EYE", ElementType::EVIL_EYE)
        .value("EVIL_EYE_AWAKE", ElementType::EVIL_EYE_AWAKE)
        .value("WRAITHWING", ElementType::WRAITHWING)
        .value("SPIDER", ElementType::SPIDER)
        .value("GOBLIN", ElementType::GOBLIN)
        .value("BRAIN", ElementType::BRAIN)
        .value("TAR_BABY", ElementType::TAR_BABY)
        .value("MIMIC", ElementType::MIMIC)
        .value("MIMIC_SWORD", ElementType::MIMIC_SWORD)
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
        .def(pybind11::init<ElementType, Direction, OrbEffects, std::optional<int>>(),
             pybind11::arg("element_type") = ElementType::NOTHING,
             pybind11::arg("direction") = Direction::NONE,
             pybind11::arg("orb_effects") = OrbEffects(),
             pybind11::arg("turn_order") = std::nullopt)
        .def_readwrite("element_type", &Element::type)
        .def_readwrite("direction", &Element::direction)
        .def_readwrite("orb_effects", &Element::orbEffects)
        .def_readwrite("turn_order", &Element::turnOrder);

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

    pybind11::class_<Room>(m, "Room", R"docstr(
A representation of a room.

A room is assumed to start at turn 0 if it should be played. Creating
an instance of this class that represents a room in progress should only
be done for display purposes.

Parameters
----------
tiles
    The tiles in the room, as arrays of arrays so that tiles[x][y] has
    the tile at coordinates (x, y).
)docstr")
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
        .def("find_monster_coordinates", &Room::findMonsterCoordinates, R"docstr(
Find coordinates of all monsters.

Returns
-------
Coordinates of all monsters.
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
)docstr")
        .def("monster_count", &Room::monsterCount, pybind11::arg("area") = std::nullopt, R"docstr(
Count the number of monsters.

Parameters
----------
area
    Limit the count to this set of positions. Can be None.

Returns
-------
The number of monsters.
)docstr")
        .def("is_conquered", &Room::isConquered, R"docstr(
Check whether the room is conquered.

Returns
-------
Whether the room is conquered.
)docstr")
        .def("make_conquered", &Room::makeConquered, R"docstr(
Set the room to a conquered state, to match when Beethro re-enters it.

Basically, remove all monsters.
)docstr");

    pybind11::class_<DerivedRoom>(m, "DerivedRoom", R"docstr(
An efficient representation of a room, but which is only valid in a specific context.

This is only valid in the context of one RoomPlayer. Comparing instances
originating from RoomPlayers playing different rooms will produce nonsensical
results.

)docstr")
        .def("get_actions", &DerivedRoom::getActions, R"docstr(
Get the actions resulting in this derived room.

Returns
-------
The actions.
)docstr");

    m.def("get_full_room", &getFullRoom, pybind11::arg("base_room"), pybind11::arg("derived_room"), R"docstr(
Get a new base room from a base room and a derived room.

Parameters
----------
base_room
    The base room.
derived_room
    The derived room.

Returns
------
The new base room.
)docstr");

    pybind11::class_<RoomPlayer>(m, "RoomPlayer", R"docstr(
This simulates taking actions in a room.

Parameters
----------
room
    The room to play.
first_entrance
    Whether this is the first time entering the room. If not, apply some
    workarounds since DROD will e.g. strike orbs before the first turn.
)docstr")
        .def(pybind11::init<Room, bool>(), pybind11::arg("room"), pybind11::arg("first_entrance") = false)
        .def("set_actions", &RoomPlayer::setActions, pybind11::arg("actions"), R"docstr(
Set the actions played in the room.

Parameters
----------
actions
    The actions.
)docstr")
        .def("get_derived_room", &RoomPlayer::getDerivedRoom, R"docstr(
Get the full played room.

Returns
----------
The derived room.
)docstr")
        .def("get_room", &RoomPlayer::getRoom, R"docstr(
Get the full played room.

Returns
----------
The room.
)docstr");

    pybind11::class_<ReachObjective>(m, "ReachObjective")
        .def(pybind11::init<std::set<Position>>(), pybind11::arg("tiles"))
        .def_readwrite("tiles", &ReachObjective::tiles);
    pybind11::class_<StabObjective>(m, "StabObjective")
        .def(pybind11::init<std::set<Position>>(), pybind11::arg("tiles"))
        .def_readwrite("tiles", &StabObjective::tiles);
    pybind11::class_<MonsterCountObjective>(m, "MonsterCountObjective")
        .def(pybind11::init<int, bool>(), pybind11::arg("monsters"), pybind11::arg("allow_less") = true)
        .def_readwrite("monsters", &MonsterCountObjective::monsters)
        .def_readwrite("allow_less", &MonsterCountObjective::allowLess);
    pybind11::class_<OrObjective>(m, "OrObjective")
        .def(pybind11::init<std::vector<Objective>>(), pybind11::arg("objectives"))
        .def_readwrite("objectives", &OrObjective::objectives);

    pybind11::enum_<FailureReason>(m, "FailureReason")
        .value("NO_FAILURE", FailureReason::NO_FAILURE)
        .value("FAILED_PRECHECK", FailureReason::FAILED_PRECHECK)
        .value("ITERATION_LIMIT_REACHED", FailureReason::ITERATION_LIMIT_REACHED)
        .value("EXHAUSTED_FRONTIER", FailureReason::EXHAUSTED_FRONTIER);

    addSearcher<Position, Action>(m, "SearcherPositionAction", "ProblemPositionAction", "SolutionPositionAction");
    addSearcher<DerivedRoom, Objective>(m, "SearcherDerivedRoomObjective", "ProblemDerivedRoomObjective", "SolutionDerivedRoomObjective");
    addSearcher<DerivedRoom, Action>(m, "SearcherDerivedRoomAction", "ProblemDerivedRoomAction", "SolutionDerivedRoomAction");

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
)docstr")
        .def(pybind11::init<Position, Room, std::set<Position>>(),
             pybind11::arg("start_position"),
             pybind11::arg("room"),
             pybind11::arg("goals"));
    pybind11::class_<PlanningProblem, Problem<DerivedRoom, Objective>>(m, "PlanningProblem", R"docstr(
A problem for reaching an objective in a room, on a high level with intermediate objectives.

Parameters
----------
objective
    The goal objective.
objective_reacher
    An objective reacher to keep track of the direct solutions.
    Can be used to put together a complete solution from the
    high-level steps.
)docstr")
        .def(pybind11::init<Objective, ObjectiveReacher *>(),
             pybind11::arg("objective"),
             pybind11::arg("objective_reacher"));
    pybind11::class_<DerivedRoomProblem, Problem<DerivedRoom, Action>>(m, "DerivedRoomProblem", R"docstr(
A problem for reaching an objective in a room.

Parameters
----------
room_player
    A room player that's playing the room to reach the objective in.
starting_room
    The room to start searching from.
objective
    The objective.
)docstr")
        .def(pybind11::init<RoomPlayer *, DerivedRoom, Objective>(),
             pybind11::arg("room_player"),
             pybind11::arg("starting_room"),
             pybind11::arg("objective"));

    pybind11::enum_<ObjectiveReacherPhase>(m, "ObjectiveReacherPhase")
        .value("NOTHING", ObjectiveReacherPhase::NOTHING)
        .value("CHECK_CACHE", ObjectiveReacherPhase::CHECK_CACHE)
        .value("PATHFIND", ObjectiveReacherPhase::PATHFIND)
        .value("SIMULATE_ROOM", ObjectiveReacherPhase::SIMULATE_ROOM)
        .value("FINISHED", ObjectiveReacherPhase::FINISHED)
        .export_values();

    pybind11::class_<ObjectiveReacher>(m, "ObjectiveReacher", R"docstr(
Find solutions to directly reach objectives in a room.

Finding a solution is done through several phases and sanity checks,
for efficiency. Also caches found solutions.

Parameters
----------
room
    The room to find solutions in.
)docstr")
        .def(pybind11::init<Room>(), pybind11::arg("room"))
        .def("get_room_player",
             &ObjectiveReacher::getRoomPlayer,
             pybind11::return_value_policy::reference,
             R"docstr(
Get the room player.

Returns
-------
The room player.
)docstr")
        .def("find_solution", &ObjectiveReacher::findSolution, pybind11::arg("room"), pybind11::arg("objective"), R"docstr(
Find a solution to reach the given objective in the given room.

This is all you need when using this class normally. The other methods are for
inspecting the algorithm.

Parameters
----------
room
    The room.
objective
    The objective to reach. 
)docstr")
        .def("start", &ObjectiveReacher::start, pybind11::arg("room"), pybind11::arg("objective"), R"docstr(
Start the process of finding a solution.

Parameters
----------
room
    The room.
objective
    The objective to reach. 
)docstr")
        .def("next_phase", &ObjectiveReacher::nextPhase, R"docstr(
Go to the next phase.
)docstr")
        .def("get_phase", &ObjectiveReacher::getPhase, R"docstr(
Get the current phase.

Returns
-------
The phase.
)docstr")
        .def("get_solution", &ObjectiveReacher::getSolution, R"docstr(
Get the solution.

This may not exist, depending on the phase. If not, throw an exception.

Returns
-------
The solution.
)docstr")
        .def("get_pathfinding_searcher",
             &ObjectiveReacher::getPathfindingSearcher,
             pybind11::return_value_policy::reference, R"docstr(
Get the pathfinding searcher.

This may not exist, depending on the phase. If not, throw an exception.

Returns
-------
The pathfinding searcher.
)docstr")
        .def("get_room_simulation_searcher",
             &ObjectiveReacher::getRoomSimulationSearcher,
             pybind11::return_value_policy::reference, R"docstr(
Get the room simulation searcher.

This may not exist, depending on the phase. If not, throw an exception.

Returns
-------
The room simulation searcher.
)docstr");
}