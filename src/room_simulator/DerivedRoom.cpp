#include "DerivedRoom.h"
#include "RoomPlayer.h"

DerivedRoom::DerivedRoom() : actions({}),
                             player(globalRoomPlayer.findPlayer()),
                             toggledDoors({}),
                             deadPlayer(false){};

DerivedRoom::DerivedRoom(std::vector<Action> actions,
                         std::tuple<Position, Direction> player,
                         std::set<Position> toggledDoors,
                         bool deadPlayer) : actions(actions),
                                            player(player),
                                            toggledDoors(toggledDoors),
                                            deadPlayer(deadPlayer) {}

DerivedRoom DerivedRoom::getSuccessor(Action action)
{
    std::vector<Action> successorActions = this->actions;
    successorActions.push_back(action);
    globalRoomPlayer.setActions(successorActions);
    std::tuple<Position, Direction> successorPlayer = globalRoomPlayer.findPlayer();
    std::set<Position> successorToggledDoors = globalRoomPlayer.getToggledDoors();
    bool successorDeadPlayer = globalRoomPlayer.playerIsDead();
    return DerivedRoom(successorActions,
                       successorPlayer,
                       successorToggledDoors,
                       successorDeadPlayer);
}

std::tuple<Position, Direction> DerivedRoom::findPlayer()
{
    return this->player;
}

bool DerivedRoom::playerIsDead()
{
    return this->deadPlayer;
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
           otherRoom.deadPlayer == this->deadPlayer;
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
    return otherRoom.toggledDoors < this->toggledDoors;
};