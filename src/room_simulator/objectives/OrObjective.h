#ifndef DRODBOT_OROBJECTIVE_H
#define DRODBOT_OROBJECTIVE_H

#include <variant>

#include "../Room.h"
#include "../DerivedRoom.h"
#include "../typedefs.h"
#include "ReachObjective.h"
#include "StabObjective.h"
#include "MonsterCountObjective.h"

// Re-define Objective here. We can't include Objective.h because of circular imports.
// If they become out of sync, it won't compile.
class OrObjective;
typedef std::variant<ReachObjective, StabObjective, MonsterCountObjective, OrObjective> Objective;
class OrObjective
{
public:
    OrObjective(std::vector<Objective> objectives);
    bool operator<(const OrObjective) const;
    bool goalTest(Room room);
    bool goalTest(DerivedRoom room);
    int heuristic(Room room);
    int heuristic(DerivedRoom room);

    std::vector<Objective> objectives;
};

#endif // DRODBOT_OROBJECTIVE_H