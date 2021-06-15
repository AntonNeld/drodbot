#ifndef DRODBOT_ROOMPLAYER_H
#define DRODBOT_ROOMPLAYER_H

#include <optional>
#include <DRODLib/Db.h>
#include "typedefs.h"
#include "Room.h"

class RoomPlayer
{
public:
    RoomPlayer();
    void initialize();
    void setRoom(Room room, bool firstEntrance = false);
    void setRoom(Room *room, bool firstEntrance = false);
    void performAction(Action action);
    void undo();
    void setActions(std::vector<Action> newActions);
    Room getRoom();
    std::tuple<Position, Direction> findPlayer();
    std::set<Position> getToggledDoors();

private:
    CDbRoom *drodRoom;
    CDbRoom *requiredRoom;
    CDbLevel *level;
    CDbHold *hold;
    CDb *db;
    CCurrentGame *currentGame;
    // Keeping track of things for interacting with DerivedRoom
    std::optional<Room> baseRoom;
    std::vector<Action> actions;
    std::map<Position, bool> closedDoors;
    // Not to be dereferenced, only used to verify which room we are in.
    std::optional<Room *> baseRoomPointer;
};

extern RoomPlayer globalRoomPlayer;
void initGlobalRoomPlayer();

#endif // DRODBOT_ROOMPLAYER_H