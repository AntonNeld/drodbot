#ifndef DRODBOT_PATHFINDING_H
#define DRODBOT_PATHFINDING_H

#include <set>
#include "Room.h"
#include "typedefs.h"

std::vector<Action> findPath(Position start, std::set<Position> goals, Room room);

#endif // DRODBOT_PATHFINDING_H