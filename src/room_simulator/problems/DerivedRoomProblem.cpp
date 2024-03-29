#include <tuple>
#include <map>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"
#include "DerivedRoomProblem.h"
#include "../utils.h"

DerivedRoomProblem::DerivedRoomProblem(RoomPlayer *roomPlayer,
                                       DerivedRoom startingRoom,
                                       Objective objective,
                                       std::map<Position, int> heuristicTiles) : roomPlayer(roomPlayer),
                                                                                 startingRoom(startingRoom),
                                                                                 objective(objective),
                                                                                 heuristicTiles(heuristicTiles){};

DerivedRoom DerivedRoomProblem::initialState()
{
    return this->startingRoom;
};

std::vector<Action> DerivedRoomProblem::actions(DerivedRoom state)
{
    std::vector<Action> actions = state.getActions();
    this->roomPlayer->setActions(actions);
    return this->roomPlayer->getPossibleActions();
};

DerivedRoom DerivedRoomProblem::result(DerivedRoom state, Action action)
{
    std::vector<Action> actions = state.getActions();
    actions.push_back(action);
    this->roomPlayer->setActions(actions);
    return this->roomPlayer->getDerivedRoom();
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