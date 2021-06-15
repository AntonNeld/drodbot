#include <stdexcept>

#include "Room.h"
#include "utils.h"

Room::Room() : tiles(Tiles()), deadPlayer(false) {}

Room::Room(Tiles tiles, bool deadPlayer) : tiles(tiles), deadPlayer(deadPlayer){};

Room Room::copy()
{
    return Room(this->tiles, this->deadPlayer);
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

std::tuple<Position, Direction> Room::findPlayer()
{
    std::vector<Position> playerCoords = this->findCoordinates(ElementType::BEETHRO);
    if (playerCoords.size() == 0)
    {
        throw std::runtime_error("Cannot find Beethro");
    }
    else if (playerCoords.size() > 1)
    {
        throw std::runtime_error("Too many Beethros");
    }
    Direction direction = this->getTile(playerCoords[0]).monster.direction;
    return std::make_tuple(playerCoords[0], direction);
}

bool Room::isPassable(int x, int y)
{
    // Can't go outside the room
    if (x < 0 || x > 37 || y < 0 || y > 31)
    {
        return false;
    }
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

bool Room::isPassable(Position position, Direction fromDirection)
{
    if (!isPassable(std::get<0>(position), std::get<1>(position)))
    {
        return false;
    }
    Tile thisTile = this->getTile(position);
    if (thisTile.floorControl.type == ElementType::FORCE_ARROW)
    {
        Direction direction = thisTile.floorControl.direction;
        if (direction == oppositeDirection(fromDirection) ||
            direction == clockwiseDirection(oppositeDirection(fromDirection)) ||
            direction == counterClockwiseDirection(oppositeDirection(fromDirection)))
        {
            return false;
        }
    }
    Tile fromTile = this->getTile(positionInDirection(position, oppositeDirection(fromDirection)));
    if (fromTile.floorControl.type == ElementType::FORCE_ARROW)
    {
        Direction direction = fromTile.floorControl.direction;
        if (direction == oppositeDirection(fromDirection) ||
            direction == clockwiseDirection(oppositeDirection(fromDirection)) ||
            direction == counterClockwiseDirection(oppositeDirection(fromDirection)))
        {
            return false;
        }
    }
    return true;
}

bool Room::playerIsDead()
{
    return this->deadPlayer;
}

bool Room::operator==(const Room otherRoom) const
{
    // TODO: In some cases the turn number also matters. Possibly only modulo 30.
    if (otherRoom.deadPlayer != this->deadPlayer)
    {
        return false;
    }
    for (int x = 0; x < 38; x++)
    {
        for (int y = 0; y < 32; y++)
        {
            Tile thisTile = this->tiles[x][y];
            Tile otherTile = otherRoom.tiles[x][y];
            if (!(thisTile == otherTile))
            {
                return false;
            }
        }
    }
    return true;
};

bool Room::operator<(const Room otherRoom) const
{
    // We'll order rooms based on the tiles, beginning from the upper left
    // TODO: In some cases the turn number also matters. Possibly only modulo 30.
    if (otherRoom.deadPlayer != this->deadPlayer)
    {
        return otherRoom.deadPlayer < this->deadPlayer;
    }
    for (int x = 0; x < 38; x++)
    {
        for (int y = 0; y < 32; y++)
        {
            Tile thisTile = this->tiles[x][y];
            Tile otherTile = otherRoom.tiles[x][y];
            if (thisTile < otherTile)
            {
                return true;
            }
            if (!(thisTile == otherTile))
            {
                return false;
            }
            // If the tiles are equal, go on to the next tile
        }
    }
    return false; // Rooms are equal
};