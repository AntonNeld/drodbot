#ifndef DRODBOT_DERIVEDROOM_H
#define DRODBOT_DERIVEDROOM_H

#include <vector>
#include <set>
#include <map>
#include "typedefs.h"
#include "Room.h"

typedef std::vector<std::tuple<ElementType, Position, Direction>> Monsters;

// This class only makes sense in the context of one RoomPlayer.
// Comparing instances of DerivedRoom originating from RoomPlayers
// playing different rooms will produce nonsensical results.
class DerivedRoom
{
public:
    DerivedRoom(std::vector<Action> actions,
                std::tuple<Position, Direction> player,
                std::set<Position> toggledDoors,
                bool deadPlayer,
                bool playerLeftRoom,
                Monsters monsters);
    std::vector<Action> getActions();
    std::tuple<Position, Direction> findPlayer();
    bool playerIsDead();
    bool playerHasLeft();
    std::vector<Position> findMonsterCoordinates(std::optional<ElementType> monsterType = std::nullopt,
                                                 std::optional<std::set<Position>> area = std::nullopt);
    int monsterCount(std::optional<ElementType> monsterType = std::nullopt,
                     std::optional<std::set<Position>> area = std::nullopt);
    bool isConquered();
    bool operator==(const DerivedRoom) const;
    bool operator<(const DerivedRoom) const;

private:
    std::vector<Action> actions;
    // Things that may differentiate this room from the base:
    std::tuple<Position, Direction> player; // Player position and direction
    std::set<Position> toggledDoors;        // Doors that are not the same as in the base room
    bool deadPlayer;
    bool playerLeftRoom;
    Monsters monsters;
    // Also the number of actions taken
};

#endif // DRODBOT_DERIVEDROOM_H