#include <tuple>
#include <set>
#include <vector>
#include <array>
#include "typedefs.h"
#include "utils.h"
#include "RoomPlayer.h"

Position positionInDirection(Position position, Direction direction)
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

Direction oppositeDirection(Direction direction)
{
    switch (direction)
    {
    case Direction::N:
        return Direction::S;
    case Direction::NE:
        return Direction::SW;
    case Direction::E:
        return Direction::W;
    case Direction::SE:
        return Direction::NW;
    case Direction::S:
        return Direction::N;
    case Direction::SW:
        return Direction::NE;
    case Direction::W:
        return Direction::E;
    case Direction::NW:
        return Direction::SE;
    default:
        return Direction::NONE;
    }
}
Direction clockwiseDirection(Direction direction)
{
    switch (direction)
    {
    case Direction::N:
        return Direction::NE;
    case Direction::NE:
        return Direction::E;
    case Direction::E:
        return Direction::SE;
    case Direction::SE:
        return Direction::S;
    case Direction::S:
        return Direction::SW;
    case Direction::SW:
        return Direction::W;
    case Direction::W:
        return Direction::NW;
    case Direction::NW:
        return Direction::N;
    default:
        return Direction::NONE;
    }
}
Direction counterClockwiseDirection(Direction direction)
{
    switch (direction)
    {
    case Direction::N:
        return Direction::NW;
    case Direction::NE:
        return Direction::N;
    case Direction::E:
        return Direction::NE;
    case Direction::SE:
        return Direction::E;
    case Direction::S:
        return Direction::SE;
    case Direction::SW:
        return Direction::S;
    case Direction::W:
        return Direction::SW;
    case Direction::NW:
        return Direction::W;
    default:
        return Direction::NONE;
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

std::set<Position> floodFill(Position position, Room room,
                             bool roomPiece,
                             bool floorControl,
                             bool checkpoint,
                             bool item,
                             bool monster)
{
    std::set<Position> affectedTiles = {};
    std::vector<Position> toCheck = {position};
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
                (!roomPiece || room.getTile(*it).roomPiece.type == room.getTile(position).roomPiece.type) &&
                (!floorControl || room.getTile(*it).floorControl.type == room.getTile(position).floorControl.type) &&
                (!checkpoint || room.getTile(*it).checkpoint.type == room.getTile(position).checkpoint.type) &&
                (!item || room.getTile(*it).item.type == room.getTile(position).item.type) &&
                (!monster || room.getTile(*it).monster.type == room.getTile(position).monster.type))
            {
                toCheck.push_back(*it);
            }
        }
    }
    return affectedTiles;
}

Room getFullRoom(Room baseRoom, DerivedRoom derivedRoom)
{
    RoomPlayer roomPlayer = RoomPlayer();
    roomPlayer.setRoom(baseRoom);
    roomPlayer.setActions(derivedRoom.getActions());
    return roomPlayer.getRoom();
}