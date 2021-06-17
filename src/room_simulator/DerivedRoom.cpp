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

std::tuple<Position, Direction> DerivedRoom::findPlayer()
{
    return this->player;
}

bool DerivedRoom::playerIsDead()
{
    return this->deadPlayer;
}

int DerivedRoom::monsterCount()
{
    return this->monsters.size();
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