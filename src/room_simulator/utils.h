#ifndef DRODBOT_UTILS_H
#define DRODBOT_UTILS_H

#include <set>

#include "Room.h"
#include "typedefs.h"

Position positionInDirection(Position position, Direction direction);
Direction oppositeDirection(Direction direction);
Direction clockwiseDirection(Direction direction);
Direction counterClockwiseDirection(Direction direction);
Position movePosition(Position start, Action action);
std::set<Position> affectedDoorTiles(Position position, Room room);

#endif // DRODBOT_UTILS_H