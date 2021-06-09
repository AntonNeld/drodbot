#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../typedefs.h"
#include "PlanningProblem.h"

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective) : room(room),
                                                        objective(objective)
{
}

Room PlanningProblem::initialState()
{
    return this->room;
}

std::set<Objective> PlanningProblem::actions(Room state)
{
    return {};
}

Room PlanningProblem::result(Room state, Objective action)
{
    return this->room;
}

bool PlanningProblem::goalTest(Room state)
{
    return false;
}

int PlanningProblem::stepCost(Room state, Objective action, Room result)
{
    return 1;
}

int PlanningProblem::heuristic(Room state)
{
    return 0;
}