#include "RoomSolver.h"
#include "RoomPlayer.h"

RoomSolver::RoomSolver(Room room,
                       Objective objective) : room(room),
                                              objective(objective)
{
    this->roomPlayer = RoomPlayer();
}

std::vector<Action> RoomSolver::findSolution()
{
    return {};
}