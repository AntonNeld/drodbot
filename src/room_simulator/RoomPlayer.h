#ifndef DRODBOT_ROOMPLAYER_H
#define DRODBOT_ROOMPLAYER_H

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
    Room getRoom();

private:
    CDbRoom *drodRoom;
    CDbRoom *requiredRoom;
    CDbLevel *level;
    CDbHold *hold;
    CDb *db;
    CCurrentGame *currentGame;
};

extern RoomPlayer globalRoomPlayer;
void initGlobalRoomPlayer();

#endif // DRODBOT_ROOMPLAYER_H