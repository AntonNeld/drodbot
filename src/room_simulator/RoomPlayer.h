#ifndef DRODBOT_ROOMPLAYER_H
#define DRODBOT_ROOMPLAYER_H

#include <DRODLib/Db.h>

class RoomPlayer
{
public:
    RoomPlayer();
    void initialize();
    void setRoom(int roomType);
    void performAction();
    int getRoom();

private:
    CDbRoom *room;
    CDbLevel *level;
    CDbHold *hold;
    CDb *db;
    CCurrentGame *currentGame;
};

#endif // DRODBOT_ROOMPLAYER_H