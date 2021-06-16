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
    void performAction(Action action);
    void undo();
    void setActions(std::vector<Action> newActions);
    Room getRoom();
    void release();
    std::tuple<Position, Direction> findPlayer();
    bool playerIsDead();
    std::set<Position> getToggledDoors();
    std::map<int, std::tuple<ElementType, Position, Direction>> getMonsters();

private:
    CDbRoom *drodRoom;
    CDbRoom *requiredRoom;
    CDbLevel *level;
    CDbHold *hold;
    CDb *db;
    CCurrentGame *currentGame;
    // Only one caller can use a room player at a time.
    // A room player is claimed by setRoom() and released by release()
    bool claimed;
    // Keeping track of things for interacting with DerivedRoom
    std::optional<Room> baseRoom;
    std::vector<Action> actions;
    std::set<Position> doors;
    std::map<int, std::tuple<ElementType, Position, Direction>> monsters;
};

extern RoomPlayer globalRoomPlayer;
void initGlobalRoomPlayer();

#endif // DRODBOT_ROOMPLAYER_H