#include "Room.h"

Room::Room(Tiles tiles)
{
    this->tiles = tiles;
}

Room Room::copy()
{
    return Room(this->tiles);
}