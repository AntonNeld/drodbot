#include "StabObjective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "../utils.h"

StabObjective::StabObjective(
    std::set<Position> tiles) : tiles(tiles){};

bool StabObjective::operator<(const StabObjective other) const
{
    return this->tiles < other.tiles;
};

bool StabObjective::goalTest(Room room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    Direction direction = std::get<1>(player);
    Position swordPosition = positionInDirection(position, direction);
    return this->tiles.find(swordPosition) != this->tiles.end();
}

bool StabObjective::goalTest(DerivedRoom room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    Direction direction = std::get<1>(player);
    Position swordPosition = positionInDirection(position, direction);
    return this->tiles.find(swordPosition) != this->tiles.end();
}