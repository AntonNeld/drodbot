#include <stdexcept>

#include "Objective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "ReachObjective.h"
#include "StabObjective.h"

bool objectiveFulfilled(Objective objective, Room room)
{
    if (ReachObjective *obj = std::get_if<ReachObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    else if (StabObjective *obj = std::get_if<StabObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    else if (MonsterCountObjective *obj = std::get_if<MonsterCountObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    throw std::invalid_argument("Unknown objective type");
}

bool objectiveFulfilled(Objective objective, DerivedRoom room)
{
    if (ReachObjective *obj = std::get_if<ReachObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    else if (StabObjective *obj = std::get_if<StabObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    else if (MonsterCountObjective *obj = std::get_if<MonsterCountObjective>(&objective))
    {
        return obj->goalTest(room);
    }
    throw std::invalid_argument("Unknown objective type");
}

int objectiveHeuristic(Objective objective, DerivedRoom room)
{
    if (ReachObjective *obj = std::get_if<ReachObjective>(&objective))
    {
        return obj->heuristic(room);
    }
    else if (StabObjective *obj = std::get_if<StabObjective>(&objective))
    {
        return obj->heuristic(room);
    }
    else if (MonsterCountObjective *obj = std::get_if<MonsterCountObjective>(&objective))
    {
        return obj->heuristic(room);
    }
    throw std::invalid_argument("Unknown objective type");
}