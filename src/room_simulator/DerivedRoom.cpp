#include "DerivedRoom.h"
#include "RoomPlayer.h"

DerivedRoom::DerivedRoom(Room *baseRoom) : baseRoom(baseRoom),
                                           actions({}),
                                           player(baseRoom->findPlayer()),
                                           toggledDoors({}),
                                           deadPlayer(false){};

DerivedRoom::DerivedRoom(Room *baseRoom,
                         std::vector<Action> actions,
                         std::tuple<Position, Direction> player,
                         std::set<Position> toggledDoors,
                         bool deadPlayer) : baseRoom(baseRoom),
                                            actions(actions),
                                            player(player),
                                            toggledDoors(toggledDoors),
                                            deadPlayer(deadPlayer) {}

DerivedRoom DerivedRoom::getSuccessor(Action action)
{
    std::vector<Action> successorActions = this->actions;
    successorActions.push_back(action);
    globalRoomPlayer.setRoom(this->baseRoom);
    globalRoomPlayer.setActions(successorActions);
    std::tuple<Position, Direction> successorPlayer = globalRoomPlayer.findPlayer();
    std::set<Position> successorToggledDoors = globalRoomPlayer.getToggledDoors();
    bool successorDeadPlayer = globalRoomPlayer.playerIsDead();
    return DerivedRoom(this->baseRoom,
                       successorActions,
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
    globalRoomPlayer.setRoom(this->baseRoom);
    globalRoomPlayer.setActions(this->actions);
    return globalRoomPlayer.getRoom();
}

bool DerivedRoom::operator==(const DerivedRoom otherRoom) const
{
    bool sameBase = otherRoom.baseRoom == this->baseRoom || *otherRoom.baseRoom == *this->baseRoom;
    return sameBase &&
           otherRoom.player == this->player &&
           otherRoom.toggledDoors == this->toggledDoors &&
           otherRoom.deadPlayer == this->deadPlayer;
};

bool DerivedRoom::operator<(const DerivedRoom otherRoom) const
{
    // Difference in base rooms take precedence. In most (all?) cases, the pointers point
    // to the same room and we don't need to compare the rooms.
    bool sameBase = otherRoom.baseRoom == this->baseRoom || *otherRoom.baseRoom == *this->baseRoom;
    if (!sameBase)
    {
        return *otherRoom.baseRoom < *this->baseRoom;
    }
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