#include "../Room.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "RoomProblem.h"

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
    std::tuple<Position, Direction> pair = this->room.findPlayer();
    Position position = std::get<0>(pair);
    Direction direction = std::get<1>(pair);
    if (this->objective.swordAtTile)
    {
        int x = std::get<0>(position);
        int y = std::get<1>(position);
        switch (direction)
        {
        case Direction::E:
            position = {x + 1, y};
        case Direction::SE:
            position = {x + 1, y + 1};
        case Direction::S:
            position = {x, y + 1};
        case Direction::SW:
            position = {x - 1, y + 1};
        case Direction::W:
            position = {x - 1, y};
        case Direction::NW:
            position = {x - 1, y - 1};
        case Direction::N:
            position = {x, y - 1};
        case Direction::NE:
            position = {x + 1, y - 1};
        default:
            position = {x, y};
        }
    }
    return this->objective.tiles.find(position) != objective.tiles.end();
}

int RoomProblem::stepCost(Room state, Action action, Room result)
{
    return 1;
}
