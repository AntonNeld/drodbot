#ifndef DRODBOT_OBJECTIVE_H
#define DRODBOT_OBJECTIVE_H

#include <variant>

#include "../Room.h"
#include "../DerivedRoom.h"
#include "ReachObjective.h"
#include "StabObjective.h"
#include "MonsterCountObjective.h"

typedef std::variant<ReachObjective, StabObjective, MonsterCountObjective> Objective;

bool objectiveFulfilled(Objective objective, Room room);
bool objectiveFulfilled(Objective objective, DerivedRoom room);

#endif // DRODBOT_OBJECTIVE_H