#ifndef DRODBOT_MONSTERCOUNTOBJECTIVE_H
#define DRODBOT_MONSTERCOUNTOBJECTIVE_H

#include "../Room.h"
#include "../DerivedRoom.h"
#include "../typedefs.h"

class MonsterCountObjective
{
public:
    MonsterCountObjective(int monsters,
                          bool allowLess = true,
                          std::optional<ElementType> monsterType = std::nullopt,
                          std::optional<std::set<Position>> area = std::nullopt);
    bool operator<(const MonsterCountObjective) const;
    bool goalTest(DerivedRoom room);
    int heuristic(DerivedRoom room);

    int monsters;
    bool allowLess;
    std::optional<ElementType> monsterType;
    std::optional<std::set<Position>> area;
};

#endif // DRODBOT_MONSTERCOUNTOBJECTIVE_H