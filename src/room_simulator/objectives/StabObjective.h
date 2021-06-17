#ifndef DRODBOT_STABOBJECTIVE_H
#define DRODBOT_STABOBJECTIVE_H

#include "../Room.h"
#include "../DerivedRoom.h"
#include "../typedefs.h"

class StabObjective
{
public:
    StabObjective(std::set<Position> tiles = {});
    bool operator<(const StabObjective) const;
    bool goalTest(Room room);
    bool goalTest(DerivedRoom room);

    std::set<Position> tiles;
};

#endif // DRODBOT_STABOBJECTIVE_H