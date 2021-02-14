#ifndef DRODBOT_ROOMPLAYER_H
#define DRODBOT_ROOMPLAYER_H

#include <DRODLib/Db.h>
#include "typedefs.h"

class RoomPlayer
{
public:
    RoomPlayer();
    void initialize();
    void setRoom(Room room);
    void performAction(Action action);
    int getRoom();

private:
    CDbRoom *drodRoom;
    CDbLevel *level;
    CDbHold *hold;
    CDb *db;
    CCurrentGame *currentGame;
};

#endif // DRODBOT_ROOMPLAYER_H