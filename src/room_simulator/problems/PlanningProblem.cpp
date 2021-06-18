#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../ObjectiveReacher.h"
#include "../typedefs.h"
#include "PlanningProblem.h"
#include "../objectives/StabObjective.h"
#include "../objectives/MonsterCountObjective.h"

// Helper
std::set<Objective> findAllObjectives(Room room, Objective finalObjective)
{
    // The final objective is included
    std::set<Objective> objectives = {finalObjective};
    // All orbs can be struck
    std::vector<Position> orbs = room.findCoordinates(ElementType::ORB);
    for (auto it = orbs.begin(); it != orbs.end(); ++it)
    {
        objectives.insert(StabObjective({*it}));
    }
    // Other objectives that depend on the room state may be added in actions()
    return objectives;
}

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective,
                                 ObjectiveReacher *objectiveReacher) : room(room),
                                                                       objective(objective),
                                                                       objectiveReacher(objectiveReacher),
                                                                       availableObjectives(findAllObjectives(room, objective))
{
}

Room PlanningProblem::initialState()
{
    return this->room;
}

std::set<Objective> PlanningProblem::actions(Room state)
{
    std::set<Objective> objectives = {};
    for (auto obj = this->availableObjectives.begin(); obj != this->availableObjectives.end(); ++obj)
    {
        Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, *obj);
        if (solution.exists)
        {
            objectives.insert(*obj);
        }
    }
    // Kill a monster
    int monsters = state.monsterCount();
    MonsterCountObjective killSomething = MonsterCountObjective(monsters - 1);
    Solution<Room, Action> killSolution = this->objectiveReacher->findSolution(state, killSomething);
    if (killSolution.exists)
    {
        objectives.insert(killSomething);
    }
    return objectives;
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