#include <tuple>
#include <map>
#include "../Room.h"
#include "../Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "RoomProblem.h"
#include "../utils.h"

RoomProblem::RoomProblem(Room room,
                         Objective objective,
                         std::map<Position, int> heuristicTiles) : room(room),
                                                                   objective(objective),
                                                                   heuristicTiles(heuristicTiles){};

Room RoomProblem::initialState()
{
    return this->room;
};

std::set<Action> RoomProblem::actions(Room state)
{
    if (state.playerIsDead())
    {
        return {};
    }
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
    return !state.playerIsDead() && this->objective.goalTest(state);
}

int RoomProblem::stepCost(Room state, Action action, Room result)
{
    return 1;
}

int RoomProblem::heuristic(Room state)
{
    Position playerPosition = std::get<0>(state.findPlayer());
    auto iterator = this->heuristicTiles.find(playerPosition);
    if (iterator != this->heuristicTiles.end())
    {
        return std::get<1>(*iterator);
    }
    // Let's assume all tiles not included are equally bad.
    // Note that this makes the heuristic non-admissable,
    // so the solution may not be optimal.
    return 10000;
}