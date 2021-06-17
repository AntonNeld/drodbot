#include "MonsterCountObjective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "../utils.h"

MonsterCountObjective::MonsterCountObjective(
    int monsters,
    bool allowLess) : monsters(monsters),
                      allowLess(allowLess){};

bool MonsterCountObjective::operator<(const MonsterCountObjective other) const
{
    if (this->monsters != other.monsters)
    {
        return this->monsters < other.monsters;
    }
    return this->allowLess < other.allowLess;
};

bool MonsterCountObjective::goalTest(Room room)
{
    int monsterCount = room.monsterCount();
    if (this->allowLess)
    {
        return monsterCount <= this->monsters;
    }
    else
    {
        return monsterCount == this->monsters;
    }
}

bool MonsterCountObjective::goalTest(DerivedRoom room)
{
    int monsterCount = room.monsterCount();
    if (this->allowLess)
    {
        return monsterCount <= this->monsters;
    }
    else
    {
        return monsterCount == this->monsters;
    }
}