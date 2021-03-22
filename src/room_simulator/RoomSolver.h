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
    std::vector<Action> findSolution();

private:
    RoomPlayer roomPlayer;
    Room room;
    Objective objective;
};

#endif // DRODBOT_ROOMSOLVER_H