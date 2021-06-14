#ifndef DRODBOT_DERIVEDROOM_H
#define DRODBOT_DERIVEDROOM_H

#include <vector>
#include "typedefs.h"
#include "Room.h"

class DerivedRoom
{
public:
    DerivedRoom(Room *baseRoom);
    DerivedRoom(Room *baseRoom, std::vector<Action> actions, std::tuple<Position, Direction> player);
    DerivedRoom getSuccessor(Action action);
    std::tuple<Position, Direction> findPlayer();
    Room getFullRoom();
    bool operator==(const DerivedRoom) const;
    bool operator<(const DerivedRoom) const;

private:
    Room *baseRoom;
    std::vector<Action> actions;
    std::tuple<Position, Direction> player;
};

#endif // DRODBOT_DERIVEDROOM_H