#include "Room.h"

Room::Room(Tiles tiles)
{
    this->tiles = tiles;
}

Room Room::copy()
{
    return Room(this->tiles);
}

Tile Room::tileAt(Position position)
{
    int x = std::get<0>(position);
    int y = std::get<1>(position);
    return this->tiles[x][y];
}