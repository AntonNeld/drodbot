#ifndef DRODBOT_PATHFINDING_H
#define DRODBOT_PATHFINDING_H

#include <vector>
#include "Room.h"
#include "typedefs.h"

std::vector<Action> findPath(Position start, std::vector<Position> goals, Room room);

#endif // DRODBOT_PATHFINDING_H