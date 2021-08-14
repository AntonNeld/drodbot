#ifndef DRODBOT_OBJECTIVE_H
#define DRODBOT_OBJECTIVE_H

#include <variant>

#include "../Room.h"
#include "../DerivedRoom.h"
#include "ReachObjective.h"
#include "StabObjective.h"
#include "MonsterCountObjective.h"
#include "OrObjective.h"

typedef std::variant<ReachObjective, StabObjective, MonsterCountObjective, OrObjective> Objective;

bool objectiveFulfilled(Objective objective, DerivedRoom room);

int objectiveHeuristic(Objective objective, DerivedRoom room);

#endif // DRODBOT_OBJECTIVE_H