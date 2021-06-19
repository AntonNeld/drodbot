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

int StabObjective::heuristic(DerivedRoom room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    Direction direction = std::get<1>(player);
    Position swordPosition = positionInDirection(position, direction);
    // Distance to nearest goal, disregarding obstacles
    int x = std::get<0>(swordPosition);
    int y = std::get<1>(swordPosition);
    int closestDistance = 37; // Largest possible distance
    for (auto it = this->tiles.begin(); it != this->tiles.end(); ++it)
    {
        int goalX = std::get<0>(*it);
        int goalY = std::get<1>(*it);
        int distance = std::max<int>(std::abs(goalX - x), std::abs(goalY - y));
        if (distance < closestDistance)
        {
            closestDistance = distance;
        }
    }
    return closestDistance;
}