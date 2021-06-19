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

int ReachObjective::heuristic(DerivedRoom room)
{
    std::tuple<Position, Direction> player = room.findPlayer();
    Position position = std::get<0>(player);
    // Distance to nearest goal, disregarding obstacles
    int x = std::get<0>(position);
    int y = std::get<1>(position);
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