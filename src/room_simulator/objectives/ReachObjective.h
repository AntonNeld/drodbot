#ifndef DRODBOT_REACHOBJECTIVE_H
#define DRODBOT_REACHOBJECTIVE_H

#include "../Room.h"
#include "../DerivedRoom.h"
#include "../typedefs.h"

class ReachObjective
{
public:
    ReachObjective(std::set<Position> tiles = {});
    bool operator<(const ReachObjective) const;
    bool goalTest(Room room);
    bool goalTest(DerivedRoom room);
    int heuristic(Room room);
    int heuristic(DerivedRoom room);

    std::set<Position> tiles;
};

#endif // DRODBOT_REACHOBJECTIVE_H