#ifndef DRODBOT_OBJECTIVEREACHER_H
#define DRODBOT_OBJECTIVEREACHER_H

#include <tuple>
#include <vector>
#include <map>
#include "typedefs.h"
#include "Room.h"
#include "Objective.h"

class ObjectiveReacher
{
public:
    ObjectiveReacher();
    Solution<Room, Action> findSolution(Room room, Objective objective);

private:
    std::map<std::tuple<Room, Objective>, Solution<Room, Action>> cachedSolutions;
};

#endif // DRODBOT_OBJECTIVEREACHER_H