#include "DerivedRoom.h"
#include "RoomPlayer.h"

DerivedRoom::DerivedRoom(Room *baseRoom) : baseRoom(baseRoom),
                                           actions({}),
                                           player(baseRoom->findPlayer()),
                                           toggledDoors({}){};

DerivedRoom::DerivedRoom(Room *baseRoom,
                         std::vector<Action> actions,
                         std::tuple<Position, Direction> player,
                         std::set<Position> toggledDoors) : baseRoom(baseRoom),
                                                            actions(actions),
                                                            player(player),
                                                            toggledDoors(toggledDoors) {}

DerivedRoom DerivedRoom::getSuccessor(Action action)
{
    std::vector<Action> successorActions = this->actions;
    successorActions.push_back(action);
    globalRoomPlayer.setRoom(this->baseRoom);
    globalRoomPlayer.setActions(successorActions);
    std::tuple<Position, Direction> player = globalRoomPlayer.findPlayer();
    std::set<Position> successorToggledDoors = globalRoomPlayer.getToggledDoors();
    return DerivedRoom(this->baseRoom, successorActions, player, successorToggledDoors);
}

std::tuple<Position, Direction> DerivedRoom::findPlayer()
{
    return this->player;
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
           otherRoom.toggledDoors == this->toggledDoors;
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
    return otherRoom.toggledDoors < this->toggledDoors;
};