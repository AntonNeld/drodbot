#include "DerivedRoom.h"
#include "RoomPlayer.h"

DerivedRoom::DerivedRoom() : actions({}),
                             player(globalRoomPlayer.findPlayer()),
                             toggledDoors({}),
                             deadPlayer(false),
                             monsters(globalRoomPlayer.getMonsters()){};

DerivedRoom::DerivedRoom(std::vector<Action> actions,
                         std::tuple<Position, Direction> player,
                         std::set<Position> toggledDoors,
                         bool deadPlayer,
                         Monsters monsters) : actions(actions),
                                              player(player),
                                              toggledDoors(toggledDoors),
                                              deadPlayer(deadPlayer),
                                              monsters(monsters){};

DerivedRoom DerivedRoom::getSuccessor(Action action)
{
    std::vector<Action> successorActions = this->actions;
    successorActions.push_back(action);
    globalRoomPlayer.setActions(successorActions);
    std::tuple<Position, Direction> successorPlayer = globalRoomPlayer.findPlayer();
    std::set<Position> successorToggledDoors = globalRoomPlayer.getToggledDoors();
    bool successorDeadPlayer = globalRoomPlayer.playerIsDead();
    Monsters successorMonsters = globalRoomPlayer.getMonsters();
    return DerivedRoom(successorActions,
                       successorPlayer,
                       successorToggledDoors,
                       successorDeadPlayer,
                       successorMonsters);
}

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

Room DerivedRoom::getFullRoom()
{
    globalRoomPlayer.setActions(this->actions);
    return globalRoomPlayer.getRoom();
}

bool DerivedRoom::operator==(const DerivedRoom otherRoom) const
{
    return otherRoom.player == this->player &&
           otherRoom.toggledDoors == this->toggledDoors &&
           otherRoom.deadPlayer == this->deadPlayer &&
           otherRoom.monsters == this->monsters;
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
    return false;
};