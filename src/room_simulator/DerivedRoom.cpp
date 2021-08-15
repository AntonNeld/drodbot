#include "DerivedRoom.h"

DerivedRoom::DerivedRoom(std::vector<Action> actions,
                         std::tuple<Position, Direction> player,
                         std::set<Position> toggledDoors,
                         bool deadPlayer,
                         bool playerLeftRoom,
                         Monsters monsters) : actions(actions),
                                              player(player),
                                              toggledDoors(toggledDoors),
                                              deadPlayer(deadPlayer),
                                              playerLeftRoom(playerLeftRoom),
                                              monsters(monsters){};

std::vector<Action> DerivedRoom::getActions()
{
    return this->actions;
}

std::tuple<Position, Direction> DerivedRoom::findPlayer()
{
    return this->player;
}

bool DerivedRoom::playerIsDead()
{
    return this->deadPlayer;
}

bool DerivedRoom::playerHasLeft()
{
    return this->playerLeftRoom;
}

std::vector<Position> DerivedRoom::findMonsterCoordinates(std::optional<ElementType> monsterType,
                                                          std::optional<std::set<Position>> area)
{
    std::vector<Position> monsterCoords = {};
    for (auto it = this->monsters.begin(); it != this->monsters.end(); ++it)
    {
        if (monsterType && monsterType.value() != std::get<0>(*it))
        {
            continue;
        }
        if (area && !area.value().contains(std::get<1>(*it)))
        {
            continue;
        }
        monsterCoords.push_back(std::get<1>(*it));
    }
    return monsterCoords;
}

int DerivedRoom::monsterCount(std::optional<ElementType> monsterType,
                              std::optional<std::set<Position>> area)
{
    if (!area && !monsterType)
    {
        return this->monsters.size();
    }
    int monsterCount = 0;
    for (auto it = this->monsters.begin(); it != this->monsters.end(); ++it)
    {
        if (monsterType && monsterType.value() != std::get<0>(*it))
        {
            continue;
        }
        if (area && !area.value().contains(std::get<1>(*it)))
        {
            continue;
        }
        monsterCount++;
    }
    return monsterCount;
}

bool DerivedRoom::isConquered()
{
    return this->monsterCount() == 0;
}

bool DerivedRoom::operator==(const DerivedRoom otherRoom) const
{
    // TODO: Turn numbers
    return otherRoom.player == this->player &&
           otherRoom.toggledDoors == this->toggledDoors &&
           otherRoom.deadPlayer == this->deadPlayer &&
           otherRoom.monsters == this->monsters;
};

bool DerivedRoom::operator<(const DerivedRoom otherRoom) const
{
    // TODO: Turn numbers
    if (otherRoom.player != this->player)
    {
        return otherRoom.player < this->player;
    }
    if (otherRoom.deadPlayer != this->deadPlayer)
    {
        return otherRoom.deadPlayer < this->deadPlayer;
    }
    if (otherRoom.toggledDoors != this->toggledDoors)
    {
        return otherRoom.toggledDoors < this->toggledDoors;
    }
    if (otherRoom.monsters != this->monsters)
    {
        return otherRoom.monsters < this->monsters;
    }
    return false;
};