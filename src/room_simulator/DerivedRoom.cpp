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

std::vector<Position> DerivedRoom::findMonsterCoordinates(std::optional<std::set<Position>> area)
{
    std::vector<Position> monsterCoords = {};
    for (auto it = this->monsters.begin(); it != this->monsters.end(); ++it)
    {
        if (!area || area.value().contains(std::get<1>(*it)))
        {
            monsterCoords.push_back(std::get<1>(*it));
        }
    }
    return monsterCoords;
}

int DerivedRoom::monsterCount(std::optional<std::set<Position>> area)
{
    if (!area)
    {
        return this->monsters.size();
    }
    int monsterCount = 0;
    for (auto it = this->monsters.begin(); it != this->monsters.end(); ++it)
    {
        if (area.value().contains(std::get<1>(*it)))
        {
            monsterCount++;
        }
    }
    return monsterCount;
}

bool DerivedRoom::isConquered()
{
    return this->monsterCount() == 0;
}

bool DerivedRoom::operator==(const DerivedRoom otherRoom) const
{
    return otherRoom.player == this->player &&
           otherRoom.toggledDoors == this->toggledDoors &&
           otherRoom.deadPlayer == this->deadPlayer &&
           otherRoom.monsters == this->monsters &&
           otherRoom.actions.size() == this->actions.size();
};

bool DerivedRoom::operator<(const DerivedRoom otherRoom) const
{

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
    if (otherRoom.actions.size() != this->actions.size())
    {
        return otherRoom.actions.size() < this->actions.size();
    }
    return false;
};