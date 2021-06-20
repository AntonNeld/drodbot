#ifndef DRODBOT_DERIVEDROOM_H
#define DRODBOT_DERIVEDROOM_H

#include <vector>
#include <set>
#include <map>
#include "typedefs.h"
#include "Room.h"

typedef std::vector<std::tuple<ElementType, Position, Direction>> Monsters;

// This class only makes sense in the context of one search,
// when the room played in globalRoomPlayer does not change.
// Working with an instance of this after the globally played
// room has changed will break.
class DerivedRoom
{
public:
    DerivedRoom();
    DerivedRoom(std::vector<Action> actions,
                std::tuple<Position, Direction> player,
                std::set<Position> toggledDoors,
                bool deadPlayer,
                Monsters monsters);
    DerivedRoom getSuccessor(Action action);
    std::tuple<Position, Direction> findPlayer();
    bool playerIsDead();
    int monsterCount(std::optional<std::set<Position>> area = std::nullopt);
    bool isConquered();
    Room getFullRoom();
    bool operator==(const DerivedRoom) const;
    bool operator<(const DerivedRoom) const;

private:
    std::vector<Action> actions;
    // Things that may differentiate this room from the base:
    std::tuple<Position, Direction> player; // Player position and direction
    std::set<Position> toggledDoors;        // Doors that are not the same as in the base room
    bool deadPlayer;
    Monsters monsters;
};

#endif // DRODBOT_DERIVEDROOM_H