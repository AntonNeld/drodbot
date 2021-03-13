#ifndef DRODBOT_ROOM_H
#define DRODBOT_ROOM_H

#include <array>
#include "typedefs.h"

// A column in a room.
typedef std::array<Tile, 32> Column;

// A representation of a room that can be imported/exported from/to Python code.
typedef std::array<Column, 38> Tiles;

class Room
{
public:
    Room(Tiles tiles);
    Tiles tiles;
};

#endif // DRODBOT_ROOM_H