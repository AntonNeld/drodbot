#include "RoomSolver.h"
#include "RoomPlayer.h"
#include "pathfinding.h"

RoomSolver::RoomSolver(Room room,
                       Objective objective) : room(room),
                                              objective(objective)
{
    this->roomPlayer = RoomPlayer();
}

std::vector<Action> RoomSolver::findSolution()
{
    std::tuple<Position, Direction> player = this->room.findPlayer();
    Position start = std::get<0>(player);
    return findPath(start, this->objective.tiles, this->room);
}