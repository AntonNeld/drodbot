#ifndef DRODBOT_DERIVEDROOM_H
#define DRODBOT_DERIVEDROOM_H

#include <vector>
#include <set>
#include "typedefs.h"
#include "Room.h"

class DerivedRoom
{
public:
    DerivedRoom(Room *baseRoom);
    DerivedRoom(Room *baseRoom,
                std::vector<Action> actions,
                std::tuple<Position, Direction> player,
                std::set<Position> toggledDoors);
    DerivedRoom getSuccessor(Action action);
    std::tuple<Position, Direction> findPlayer();
    Room getFullRoom();
    bool operator==(const DerivedRoom) const;
    bool operator<(const DerivedRoom) const;

private:
    Room *baseRoom;
    std::vector<Action> actions;
    // Things that may differentiate this room from the base:
    std::tuple<Position, Direction> player; // Player position and direction
    std::set<Position> toggledDoors;        // Doors that are not the same as in the base room
};

#endif // DRODBOT_DERIVEDROOM_H