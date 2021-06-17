#include <stdexcept>

#include "Objective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "ReachObjective.h"
#include "StabObjective.h"

bool objectiveFulfilled(Objective objective, Room room)
{
    if (ReachObjective *reachObj = std::get_if<ReachObjective>(&objective))
    {
        return reachObj->goalTest(room);
    }
    else if (StabObjective *stabObj = std::get_if<StabObjective>(&objective))
    {
        return stabObj->goalTest(room);
    }
    throw std::invalid_argument("Unknown objective type");
}

bool objectiveFulfilled(Objective objective, DerivedRoom room)
{
    if (ReachObjective *reachObj = std::get_if<ReachObjective>(&objective))
    {
        return reachObj->goalTest(room);
    }
    else if (StabObjective *stabObj = std::get_if<StabObjective>(&objective))
    {
        return stabObj->goalTest(room);
    }
    throw std::invalid_argument("Unknown objective type");
}
