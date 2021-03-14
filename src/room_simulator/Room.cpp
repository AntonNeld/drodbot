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

std::vector<Position> Room::findCoordinates(ElementType elementType)
{
    std::vector<Position> coords;
    for (int x = 0; x < 38; x += 1)
    {
        for (int y = 0; y < 32; y += 1)
        {
            Tile tile = this->tiles[x][y];
            if (tile.roomPiece.type == elementType ||
                tile.floorControl.type == elementType ||
                tile.checkpoint.type == elementType ||
                tile.item.type == elementType ||
                tile.monster.type == elementType)
            {
                coords.push_back(std::make_tuple(x, y));
            }
        }
    }
    return coords;
}

bool Room::isPassable(int x, int y)
{
    Tile tile = this->tiles[x][y];
    switch (tile.roomPiece.type)
    {
    case ElementType::WALL:
    case ElementType::MASTER_WALL:
    case ElementType::YELLOW_DOOR:
    case ElementType::BLUE_DOOR:
    case ElementType::GREEN_DOOR:
    case ElementType::PIT:
        return false;
    default:
        break; // Nothing
    }
    switch (tile.item.type)
    {
    case ElementType::OBSTACLE:
    case ElementType::ORB:
        return false;
    default:
        break; // Nothing
    }
    return true;
}