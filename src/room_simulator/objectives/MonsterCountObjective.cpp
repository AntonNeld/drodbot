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
    // We're assuming we want to bring the monster count down, not up
    std::tuple<Position, Direction> player = room.findPlayer();
    Position swordPosition = positionInDirection(std::get<0>(player), std::get<1>(player));
    int x = std::get<0>(swordPosition);
    int y = std::get<1>(swordPosition);
    std::vector<Position> monsterCoords = room.findMonsterCoordinates(this->area);
    int closestDistance = 37;
    for (auto it = monsterCoords.begin(); it != monsterCoords.end(); ++it)
    {
        int monsterX = std::get<0>(*it);
        int monsterY = std::get<1>(*it);
        int distance = std::max<int>(std::abs(monsterX - x), std::abs(monsterY - y));
        if (distance < closestDistance)
        {
            closestDistance = distance;
        }
    }
    int monsterCount = monsterCoords.size();
    if (monsterCount == 0)
    {
        // If there are no monsters, we don't care about the distance
        closestDistance = 0;
    }
    // Let's prioritize being closer to monsters, and having killed
    // some (with a larger weight)
    return closestDistance + 10 * (monsterCount - this->monsters);
}