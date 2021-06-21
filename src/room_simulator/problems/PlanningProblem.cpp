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

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective,
                                 ObjectiveReacher *objectiveReacher) : room(room),
                                                                       objective(objective),
                                                                       objectiveReacher(objectiveReacher),
                                                                       orbs(room.findCoordinates(ElementType::ORB)){};

Room PlanningProblem::initialState()
{
    return this->room;
}

std::set<Objective> PlanningProblem::actions(Room state)
{
    std::set<Objective> objectives = {};
    // Always try reaching the final objective
    // TODO: May not make sense if it's something like clearing the room
    objectives.insert(this->objective);
    // Try to strike each orb
    for (auto it = this->orbs.begin(); it != this->orbs.end(); ++it)
    {
        objectives.insert(StabObjective({*it}));
    }
    // We may be far from a monster, so add an objective to either:
    // - Stab any tile which currently has a monster (to get pathfinding)
    // - Kill a monster (to stop going to the tile if we kill it early)
    std::vector<Position> monsterPositions = state.findMonsterCoordinates();
    std::set<Position> monsterPositionsSet = {};
    monsterPositionsSet.insert(monsterPositions.begin(), monsterPositions.end());
    objectives.insert(OrObjective({StabObjective(monsterPositionsSet),
                                   MonsterCountObjective(monsterPositions.size() - 1)}));
    // Only return objectives we can actually reach, but haven't reached already
    std::set<Objective> reachableObjectives = {};
    for (auto it = objectives.begin(); it != objectives.end(); ++it)
    {
        if (!objectiveFulfilled(*it, state))
        {
            Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, *it);
            if (solution.exists)
            {
                reachableObjectives.insert(*it);
            }
        }
    }
    return reachableObjectives;
}

Room PlanningProblem::result(Room state, Objective action)
{
    Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.finalState.value();
}

bool PlanningProblem::goalTest(Room state)
{
    return objectiveFulfilled(this->objective, state);
}

int PlanningProblem::stepCost(Room state, Objective action, Room result)
{
    Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.actions.value().size();
}

int PlanningProblem::heuristic(Room state)
{
    return objectiveHeuristic(this->objective, state);
}