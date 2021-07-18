#include <tuple>
#include <map>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "DerivedRoomProblem.h"
#include "../utils.h"

DerivedRoomProblem::DerivedRoomProblem(Room room,
                                       Objective objective,
                                       std::map<Position, int> heuristicTiles) : roomPlayer(RoomPlayer(room)),
                                                                                 objective(objective),
                                                                                 heuristicTiles(heuristicTiles){};

DerivedRoom DerivedRoomProblem::initialState()
{
    this->roomPlayer.setActions({});
    return this->roomPlayer.getDerivedRoom();
};

std::set<Action> DerivedRoomProblem::actions(DerivedRoom state)
{
    if (state.playerIsDead() || state.playerHasLeft())
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
    std::vector<Action> actions = state.getActions();
    actions.push_back(action);
    this->roomPlayer.setActions(actions);
    return this->roomPlayer.getDerivedRoom();
}

bool DerivedRoomProblem::goalTest(DerivedRoom state)
{
    return !state.playerIsDead() && objectiveFulfilled(this->objective, state);
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
    // If we're not in a heuristicTile, use the objective's heuristic.
    // Add a penalty to make it prefer the heuristicTiles.
    return objectiveHeuristic(this->objective, state) + 100;
}