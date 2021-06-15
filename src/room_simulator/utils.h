#ifndef DRODBOT_UTILS_H
#define DRODBOT_UTILS_H

#include <set>

#include "Room.h"
#include "typedefs.h"

Position swordPosition(Position position, Direction direction);
Position movePosition(Position start, Action action);
std::set<Position> affectedDoorTiles(Position position, Room room);

#endif // DRODBOT_UTILS_H