#ifndef DRODBOT_MONSTERCOUNTOBJECTIVE_H
#define DRODBOT_MONSTERCOUNTOBJECTIVE_H

#include "../Room.h"
#include "../DerivedRoom.h"
#include "../typedefs.h"

class MonsterCountObjective
{
public:
    MonsterCountObjective(int monsters, bool allowLess = true);
    bool operator<(const MonsterCountObjective) const;
    bool goalTest(Room room);
    bool goalTest(DerivedRoom room);

    int monsters;
    bool allowLess;
};

#endif // DRODBOT_MONSTERCOUNTOBJECTIVE_H