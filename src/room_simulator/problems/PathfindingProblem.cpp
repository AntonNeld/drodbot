#include <iostream>
#include <algorithm>
#include <array>
#include <vector>
#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../typedefs.h"
#include "../search/Problem.h"
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

std::vector<Action> PathfindingProblem::actions(Position state)
{
    // Cannot move from a stair
    if (this->room.getTile(state).roomPiece.type == ElementType::STAIRS)
    {
        return {};
    }
    std::vector<Action> actions = {};
    int x = std::get<0>(state);
    int y = std::get<1>(state);
    if (this->room.isPassableInDirection({x + 1, y}, Direction::E))
    {
        actions.push_back(Action::E);
    }
    if (this->room.isPassableInDirection({x + 1, y + 1}, Direction::SE))
    {
        actions.push_back(Action::SE);
    }
    if (this->room.isPassableInDirection({x, y + 1}, Direction::S))
    {
        actions.push_back(Action::S);
    }
    if (this->room.isPassableInDirection({x - 1, y + 1}, Direction::SW))
    {
        actions.push_back(Action::SW);
    }
    if (this->room.isPassableInDirection({x - 1, y}, Direction::W))
    {
        actions.push_back(Action::W);
    }
    if (this->room.isPassableInDirection({x - 1, y - 1}, Direction::NW))
    {
        actions.push_back(Action::NW);
    }
    if (this->room.isPassableInDirection({x, y - 1}, Direction::N))
    {
        actions.push_back(Action::N);
    }
    if (this->room.isPassableInDirection({x + 1, y - 1}, Direction::NE))
    {
        actions.push_back(Action::NE);
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

int PathfindingProblem::heuristic(Position state)
{
    // Distance to nearest goal, disregarding obstacles
    int x = std::get<0>(state);
    int y = std::get<1>(state);
    int closestDistance = 37; // Largest possible distance
    typename std::set<Position>::iterator iterator;
    for (iterator = this->goals.begin(); iterator != this->goals.end(); ++iterator)
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