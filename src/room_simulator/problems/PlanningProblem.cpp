#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../ObjectiveReacher.h"
#include "../typedefs.h"
#include "PlanningProblem.h"
#include "../objectives/StabObjective.h"
#include "../objectives/MonsterCountObjective.h"

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective,
                                 ObjectiveReacher *objectiveReacher) : room(room),
                                                                       objective(objective),
                                                                       objectiveReacher(objectiveReacher),
                                                                       orbs(room.findCoordinates(ElementType::ORB))
{
}

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
    // Go to the location of a monster
    std::vector<Position> monsters = state.findMonsterCoordinates();
    for (auto it = monsters.begin(); it != monsters.end(); ++it)
    {
        ReachObjective objective = ReachObjective({*it});
        objectives.insert(objective);
    }
    // Kill a monster
    MonsterCountObjective killSomething = MonsterCountObjective(monsters.size() - 1);
    objectives.insert(killSomething);
    // Only return objectives we can actually reach
    std::set<Objective> reachableObjectives = {};
    for (auto it = objectives.begin(); it != objectives.end(); ++it)
    {
        Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, *it);
        if (solution.exists)
        {
            reachableObjectives.insert(*it);
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
    return 0;
}