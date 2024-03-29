#ifndef DRODBOT_ROOMPLAYER_H
#define DRODBOT_ROOMPLAYER_H

#include <optional>
#include <DRODLib/Db.h>
#include "typedefs.h"
#include "Room.h"
#include "DerivedRoom.h"

class RoomPlayer
{
public:
    RoomPlayer(Room room, bool firstEntrance = false);
    ~RoomPlayer();
    std::vector<Action> getPossibleActions();
    void setActions(std::vector<Action> newActions);
    bool isPassableInDirection(Position position, Direction fromDirection);
    Room getRoom();
    DerivedRoom getDerivedRoom();

private:
    void performAction(Action action);
    void undo(unsigned long int turns);
    std::tuple<Position, Direction> findPlayer();
    bool playerIsDead();
    bool playerHasLeft();
    std::set<Position> getToggledDoors();
    std::vector<std::tuple<ElementType, Position, Direction>> getMonsters();
    CDbRoom *drodRoom;
    CCurrentGame *currentGame;
    // Keeping track of things for interacting with DerivedRoom
    Room baseRoom;
    std::vector<Action> actions;
    std::set<Position> doors;
};

void initRoomPlayerRequirements();

#endif // DRODBOT_ROOMPLAYER_H