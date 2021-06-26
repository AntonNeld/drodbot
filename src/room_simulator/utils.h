#ifndef DRODBOT_UTILS_H
#define DRODBOT_UTILS_H

#include <set>

#include "Room.h"
#include "DerivedRoom.h"
#include "typedefs.h"

Position positionInDirection(Position position, Direction direction);
Direction oppositeDirection(Direction direction);
Direction clockwiseDirection(Direction direction);
Direction counterClockwiseDirection(Direction direction);
Position movePosition(Position start, Action action);
std::set<Position> floodFill(Position position, Room room,
                             bool roomPiece = true,
                             bool floorControl = false,
                             bool checkpoint = false,
                             bool item = false,
                             bool monster = false);
Room getFullRoom(Room baseRoom, DerivedRoom derivedRoom);

#endif // DRODBOT_UTILS_H