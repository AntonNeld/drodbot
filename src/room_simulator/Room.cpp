#include "Room.h"

Room::Room(Tiles tiles)
{
    this->tiles = tiles;
}

Room Room::copy()
{
    return Room(this->tiles);
}

Tile Room::getTile(Position position)
{
    int x = std::get<0>(position);
    int y = std::get<1>(position);
    return this->tiles[x][y];
}

void Room::setTile(Position position, Tile tile)
{
    int x = std::get<0>(position);
    int y = std::get<1>(position);
    tiles[x][y] = tile;
}