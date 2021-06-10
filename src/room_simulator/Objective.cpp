#include "Objective.h"
#include "Room.h"
#include "utils.h"

Objective::Objective(
    bool swordAtTile,
    std::set<Position> tiles) : swordAtTile(swordAtTile),
                                tiles(tiles)
{
}

bool Objective::operator<(const Objective other) const
{
    if (this->swordAtTile != other.swordAtTile)
    {
        return this->swordAtTile;
    }
    if (this->tiles.size() != other.tiles.size())
    {
        return this->tiles.size() < other.tiles.size();
    }
    auto thisTilesIterator = this->tiles.begin();
    auto otherTilesIterator = other.tiles.begin();
    while (thisTilesIterator != this->tiles.end())
    {
        if (*thisTilesIterator != *otherTilesIterator)
        {
            return *thisTilesIterator < *otherTilesIterator;
        }
        ++thisTilesIterator;
        ++otherTilesIterator;
    }
    return false;
};

bool Objective::goalTest(Room room)
{
    std::tuple<Position, Direction> pair = room.findPlayer();
    Position position = std::get<0>(pair);
    Direction direction = std::get<1>(pair);
    if (this->swordAtTile)
    {
        position = swordPosition(position, direction);
    }
    return this->tiles.find(position) != this->tiles.end();
}
