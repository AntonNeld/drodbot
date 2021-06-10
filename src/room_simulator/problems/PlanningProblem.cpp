#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../Objective.h"
#include "../ObjectiveReacher.h"
#include "../typedefs.h"
#include "PlanningProblem.h"

// Helper
std::set<Objective> findAllObjectives(Room room, Objective finalObjective)
{
    // The final objective is included
    std::set<Objective> objectives = {finalObjective};
    // All orbs can be struck
    std::vector<Position> orbs = room.findCoordinates(ElementType::ORB);
    for (auto it = orbs.begin(); it != orbs.end(); ++it)
    {
        objectives.insert(Objective(true, {*it}));
    }
    return objectives;
}

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective) : room(room),
                                                        objective(objective),
                                                        objectiveReacher(ObjectiveReacher()),
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
        Solution<Room, Action> solution = this->objectiveReacher.findSolution(state, *obj);
        if (solution.exists)
        {
            objectives.insert(*obj);
        }
    }
    return objectives;
}

Room PlanningProblem::result(Room state, Objective action)
{
    Solution<Room, Action> solution = this->objectiveReacher.findSolution(state, action);
    return solution.finalState;
}

bool PlanningProblem::goalTest(Room state)
{
    return this->objective.goalTest(state);
}

int PlanningProblem::stepCost(Room state, Objective action, Room result)
{
    Solution<Room, Action> solution = this->objectiveReacher.findSolution(state, action);
    return solution.actions.size();
}

int PlanningProblem::heuristic(Room state)
{
    return 0;
}