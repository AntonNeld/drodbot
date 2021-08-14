#include "OrObjective.h"
#include "Objective.h"
#include "../Room.h"
#include "../DerivedRoom.h"

OrObjective::OrObjective(
    std::vector<Objective> objectives) : objectives(objectives){};

bool OrObjective::operator<(const OrObjective other) const
{
    return this->objectives < other.objectives;
};

bool OrObjective::goalTest(DerivedRoom room)
{
    for (auto objective : this->objectives)
    {
        if (objectiveFulfilled(objective, room))
        {
            return true;
        }
    }
    return false;
}

int OrObjective::heuristic(DerivedRoom room)
{
    return objectiveHeuristic(this->objectives.front(), room);
}