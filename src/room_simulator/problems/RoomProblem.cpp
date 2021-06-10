#include <tuple>
#include "../Room.h"
#include "../Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "RoomProblem.h"

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

RoomProblem::RoomProblem(Room room,
                         Objective objective) : room(room),
                                                objective(objective){};

Room RoomProblem::initialState()
{
    return this->room;
};

std::set<Action> RoomProblem::actions(Room state)
{
    return {Action::E,
            Action::SE,
            Action::S,
            Action::SW,
            Action::W,
            Action::NW,
            Action::N,
            Action::NE,
            Action::CW,
            Action::CCW,
            Action::WAIT};
};

Room RoomProblem::result(Room state, Action action)
{
    globalRoomPlayer.setRoom(state);
    globalRoomPlayer.performAction(action);
    return globalRoomPlayer.getRoom();
}

bool RoomProblem::goalTest(Room state)
{
    std::tuple<Position, Direction> pair = state.findPlayer();
    Position position = std::get<0>(pair);
    Direction direction = std::get<1>(pair);
    if (this->objective.swordAtTile)
    {
        position = swordPosition(position, direction);
    }
    return this->objective.tiles.find(position) != objective.tiles.end();
}

int RoomProblem::stepCost(Room state, Action action, Room result)
{
    return 1;
}

int RoomProblem::heuristic(Room state)
{
    // Distance to nearest goal, disregarding obstacles
    std::tuple<Position, Direction> pair = state.findPlayer();
    Position position = std::get<0>(pair);
    Direction direction = std::get<1>(pair);
    if (this->objective.swordAtTile)
    {
        position = swordPosition(position, direction);
    }
    int x = std::get<0>(position);
    int y = std::get<1>(position);
    int closestDistance = 37; // Largest possible distance
    typename std::set<Position>::iterator iterator;
    for (iterator = this->objective.tiles.begin(); iterator != this->objective.tiles.end(); ++iterator)
    {
        int goalX = std::get<0>(*iterator);
        int goalY = std::get<1>(*iterator);
        int distance = std::max<int>(std::abs(goalX - x), std::abs(goalY - y));
        if (distance < closestDistance)
        {
            closestDistance = distance;
        }
    }
    return closestDistance;
}