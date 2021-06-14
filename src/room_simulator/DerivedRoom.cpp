#include "DerivedRoom.h"
#include "RoomPlayer.h"

DerivedRoom::DerivedRoom(Room *baseRoom) : baseRoom(baseRoom),
                                           actions({}),
                                           player(baseRoom->findPlayer()){};

DerivedRoom::DerivedRoom(Room *baseRoom,
                         std::vector<Action> actions,
                         std::tuple<Position, Direction> player) : baseRoom(baseRoom),
                                                                   actions(actions),
                                                                   player(player) {}

DerivedRoom DerivedRoom::getSuccessor(Action action)
{
    std::vector<Action> successorActions = this->actions;
    successorActions.push_back(action);
    globalRoomPlayer.setRoom(this->baseRoom);
    globalRoomPlayer.setActions(successorActions);
    std::tuple<Position, Direction> player = globalRoomPlayer.findPlayer();
    return DerivedRoom(this->baseRoom, successorActions, player);
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
    return sameBase && otherRoom.player == this->player;
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
    // Otherwise, check the player position and direction
    return otherRoom.player < this->player;
};