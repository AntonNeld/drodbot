#include <tuple>
#include <set>
#include <vector>
#include <array>
#include "typedefs.h"
#include "utils.h"

Position swordPosition(Position position, Direction direction)
{
    int x = std::get<0>(position);
    int y = std::get<1>(position);
    switch (direction)
    {
    case Direction::E:
        return {x + 1, y};
    case Direction::SE:
        return {x + 1, y + 1};
    case Direction::S:
        return {x, y + 1};
    case Direction::SW:
        return {x - 1, y + 1};
    case Direction::W:
        return {x - 1, y};
    case Direction::NW:
        return {x - 1, y - 1};
    case Direction::N:
        return {x, y - 1};
    case Direction::NE:
        return {x + 1, y - 1};
    default:
        return {x, y};
    }
}

Position movePosition(Position start, Action action)
{
    int x = std::get<0>(start);
    int y = std::get<1>(start);
    switch (action)
    {
    case Action::E:
        return {x + 1, y};
    case Action::SE:
        return {x + 1, y + 1};
    case Action::S:
        return {x, y + 1};
    case Action::SW:
        return {x - 1, y + 1};
    case Action::W:
        return {x - 1, y};
    case Action::NW:
        return {x - 1, y - 1};
    case Action::N:
        return {x, y - 1};
    case Action::NE:
        return {x + 1, y - 1};
    default:
        return {x, y};
    }
}

std::set<Position> affectedDoorTiles(Position position, Room room)
{
    std::set<Position> affectedTiles = {};
    std::vector<Position> toCheck = {position};
    ElementType doorType = room.getTile(position).roomPiece.type;
    while (!toCheck.empty())
    {
        Position checking = toCheck.back();
        toCheck.pop_back();
        affectedTiles.insert(checking);
        int x = std::get<0>(checking);
        int y = std::get<1>(checking);
        std::array<Position, 4> newPositions{{{x + 1, y}, {x, y + 1}, {x - 1, y}, {x, y - 1}}};
        for (auto it = newPositions.begin(); it != newPositions.end(); ++it)
        {
            int newX = std::get<0>(*it);
            int newY = std::get<1>(*it);
            if (newX >= 0 && newX < 38 && newY >= 0 && newY < 32 &&
                affectedTiles.find(*it) == affectedTiles.end() &&
                room.getTile(*it).roomPiece.type == doorType)
            {
                toCheck.push_back(*it);
            }
        }
    }
    return affectedTiles;
}