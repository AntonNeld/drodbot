#include <array>
#include <vector>
#include <set>
#include "../Room.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../search/AStarSearcher.h"
#include "PathfindingProblem.h"

PathfindingProblem::PathfindingProblem(Position startPosition,
                                       Room room,
                                       std::set<Position> goals) : startPosition(startPosition),
                                                                   room(room),
                                                                   goals(goals)
{
}

Position PathfindingProblem::initialState()
{
    return this->startPosition;
}

std::set<Action> PathfindingProblem::actions(Position state)
{
    std::set<Action> actions;
    int x = std::get<0>(state);
    int y = std::get<1>(state);
    if (this->room.isPassable(x + 1, y))
    {
        actions.insert(Action::E);
    }
    if (this->room.isPassable(x + 1, y + 1))
    {
        actions.insert(Action::SE);
    }
    if (this->room.isPassable(x, y + 1))
    {
        actions.insert(Action::S);
    }
    if (this->room.isPassable(x - 1, y + 1))
    {
        actions.insert(Action::SW);
    }
    if (this->room.isPassable(x - 1, y))
    {
        actions.insert(Action::W);
    }
    if (this->room.isPassable(x - 1, y - 1))
    {
        actions.insert(Action::NW);
    }
    if (this->room.isPassable(x, y - 1))
    {
        actions.insert(Action::N);
    }
    if (this->room.isPassable(x + 1, y - 1))
    {
        actions.insert(Action::NE);
    }
    return actions;
}

Position PathfindingProblem::result(Position state, Action action)
{
    int x = std::get<0>(state);
    int y = std::get<1>(state);
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

bool PathfindingProblem::goalTest(Position state)
{
    return this->goals.find(state) != goals.end();
}

int PathfindingProblem::stepCost(Position state, Action action, Position result)
{
    return 1;
}
