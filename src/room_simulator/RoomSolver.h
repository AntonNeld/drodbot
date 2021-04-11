#ifndef DRODBOT_ROOMSOLVER_H
#define DRODBOT_ROOMSOLVER_H

#include <vector>
#include "typedefs.h"
#include "Room.h"
#include "RoomPlayer.h"

class RoomSolver
{
public:
    RoomSolver(Room room, Objective objective);
    std::vector<Action> findSolution(bool simplePathfinding = false);
    int getIterations();

private:
    Room room;
    Objective objective;
};

#endif // DRODBOT_ROOMSOLVER_H