#ifndef DRODBOT_PATHFINDING_H
#define DRODBOT_PATHFINDING_H

#include <vector>
#include "Room.h"
#include "typedefs.h"

std::vector<Action> findPath(Position start, Direction startDirection, std::vector<Position> goals, Room room, bool swordAtGoal = false);

#endif // DRODBOT_PATHFINDING_H