#include <tuple>
#include "RoomSolver.h"
#include "RoomPlayer.h"
#include "pathfinding.h"
#include "typedefs.h"
#include "search/Problem.h"
#include "search/AStarSearcher.h"
#include "problems/RoomProblem.h"

RoomSolver::RoomSolver(Room room,
                       Objective objective) : room(room),
                                              objective(objective){};

std::vector<Action> RoomSolver::findSolution(bool simplePathfinding)
{
    if (simplePathfinding)
    {
        std::tuple<Position, Direction> player = this->room.findPlayer();
        Position start = std::get<0>(player);
        return findPath(start, this->objective.tiles, this->room);
    }
    RoomProblem problem = RoomProblem(room, objective);
    AStarSearcher<Room, Action> searcher = AStarSearcher<Room, Action>(&problem);
    return searcher.findSolution();
}

int RoomSolver::getIterations()
{
    return 0;
}