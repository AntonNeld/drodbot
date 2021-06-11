#include <tuple>
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