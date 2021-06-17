#include <tuple>
#include <map>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "DerivedRoomProblem.h"
#include "../utils.h"

DerivedRoomProblem::DerivedRoomProblem(Objective objective,
                                       std::map<Position, int> heuristicTiles) : objective(objective),
                                                                                 heuristicTiles(heuristicTiles){};

DerivedRoom DerivedRoomProblem::initialState()
{
    return DerivedRoom();
};

std::set<Action> DerivedRoomProblem::actions(DerivedRoom state)
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

DerivedRoom DerivedRoomProblem::result(DerivedRoom state, Action action)
{
    return state.getSuccessor(action);
}

bool DerivedRoomProblem::goalTest(DerivedRoom state)
{
    return !state.playerIsDead() && this->objective.goalTest(state);
}

int DerivedRoomProblem::stepCost(DerivedRoom state, Action action, DerivedRoom result)
{
    return 1;
}

int DerivedRoomProblem::heuristic(DerivedRoom state)
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