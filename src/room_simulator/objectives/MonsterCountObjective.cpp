#include "MonsterCountObjective.h"
#include "../Room.h"
#include "../DerivedRoom.h"
#include "../utils.h"

MonsterCountObjective::MonsterCountObjective(
    int monsters,
    bool allowLess,
    std::optional<std::set<Position>> area) : monsters(monsters),
                                              allowLess(allowLess),
                                              area(area){};

bool MonsterCountObjective::operator<(const MonsterCountObjective other) const
{
    if (this->monsters != other.monsters)
    {
        return this->monsters < other.monsters;
    }
    if (this->allowLess != other.allowLess)
    {
        return this->allowLess < other.allowLess;
    }
    if (this->area != other.area)
    {
        return this->area < other.area;
    }
    return false; // Equal
};

bool MonsterCountObjective::goalTest(Room room)
{
    int monsterCount = room.monsterCount(this->area);
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
    int monsterCount = room.monsterCount(this->area);
    if (this->allowLess)
    {
        return monsterCount <= this->monsters;
    }
    else
    {
        return monsterCount == this->monsters;
    }
}

int MonsterCountObjective::heuristic(DerivedRoom room)
{
    int monsterCount = room.monsterCount(this->area);
    // We're assuming we want to bring the monster count down, not up
    return monsterCount - this->monsters;
}