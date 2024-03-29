#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../ObjectiveReacher.h"
#include "../typedefs.h"
#include "PlanningProblem.h"
#include "../objectives/StabObjective.h"
#include "../objectives/MonsterCountObjective.h"
#include "../utils.h"

PlanningProblem::PlanningProblem(
    Objective objective,
    ObjectiveReacher *objectiveReacher) : objective(objective),
                                          objectiveReacher(objectiveReacher),
                                          orbs(objectiveReacher->getRoomPlayer()->getRoom().findCoordinates(ElementType::ORB)){};

DerivedRoom PlanningProblem::initialState()
{
    this->objectiveReacher->getRoomPlayer()->setActions({});
    return this->objectiveReacher->getRoomPlayer()->getDerivedRoom();
}

std::vector<Objective> PlanningProblem::actions(DerivedRoom state)
{
    // Always try reaching the final objective
    // TODO: May not make sense if it's something like clearing the room
    std::vector<Objective> objectives = {this->objective};
    // Try to strike each orb
    for (auto it = this->orbs.begin(); it != this->orbs.end(); ++it)
    {
        objectives.push_back(StabObjective({*it}));
    }
    // If there are roach queens, ignore other monsters
    std::vector<Position> monsterPositions = state.findMonsterCoordinates(ElementType::ROACH_QUEEN);
    std::optional<ElementType> monsterType = ElementType::ROACH_QUEEN;
    if (monsterPositions.size() == 0)
    {
        monsterPositions = state.findMonsterCoordinates();
        monsterType = std::nullopt;
    }
    // We may be far from a monster, so (if there are monsters) add an objective to either:
    // - Stab any tile which currently has a monster (to get pathfinding)
    // - Kill a monster (to stop going to the tile if we kill it early)
    if (monsterPositions.size() > 0)
    {
        std::set<Position> monsterPositionsSet = {};
        monsterPositionsSet.insert(monsterPositions.begin(), monsterPositions.end());
        objectives.push_back(OrObjective({StabObjective(monsterPositionsSet),
                                          MonsterCountObjective(monsterPositions.size() - 1, true, monsterType)}));
    }

    // Only return objectives we can actually reach, but haven't reached already
    std::vector<Objective> reachableObjectives = {};
    for (auto it = objectives.begin(); it != objectives.end(); ++it)
    {
        if (!objectiveFulfilled(*it, state))
        {
            Solution<DerivedRoom, Action> solution = this->objectiveReacher->findSolution(state, *it);
            if (solution.exists)
            {
                reachableObjectives.push_back(*it);
            }
        }
    }
    return reachableObjectives;
}

DerivedRoom PlanningProblem::result(DerivedRoom state, Objective action)
{
    Solution<DerivedRoom, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.finalState.value();
}

bool PlanningProblem::goalTest(DerivedRoom state)
{
    return objectiveFulfilled(this->objective, state);
}

int PlanningProblem::stepCost(DerivedRoom state, Objective action, DerivedRoom result)
{
    Solution<DerivedRoom, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.actions.value().size();
}

int PlanningProblem::heuristic(DerivedRoom state)
{
    return objectiveHeuristic(this->objective, state);
}