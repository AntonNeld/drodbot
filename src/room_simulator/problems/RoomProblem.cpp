#include <tuple>
#include "../Room.h"
#include "../Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "RoomProblem.h"
#include "../utils.h"

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
    return this->objective.goalTest(state);
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