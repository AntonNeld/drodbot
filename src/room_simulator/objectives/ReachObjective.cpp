#include "ReachObjective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "../utils.h"

ReachObjective::ReachObjective(
    std::set<Position> tiles) : tiles(tiles){};

bool ReachObjective::operator<(const ReachObjective other) const
{
    return this->tiles < other.tiles;
};

bool ReachObjective::goalTest(Room room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    return this->tiles.find(position) != this->tiles.end();
}

bool ReachObjective::goalTest(DerivedRoom room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    return this->tiles.find(position) != this->tiles.end();
}