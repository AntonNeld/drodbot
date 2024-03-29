#ifndef DRODBOT_ROOM_H
#define DRODBOT_ROOM_H

#include <array>
#include <tuple>
#include <vector>
#include "typedefs.h"

typedef std::array<Tile, 32> Column;
typedef std::array<Column, 38> Tiles;
class Room
{
public:
    Room();
    Room(Tiles tiles, bool deadPlayer = false);
    Room copy();
    Tile getTile(Position position);
    void setTile(Position position, Tile tile);
    std::vector<Position> findCoordinates(ElementType elementType);
    std::vector<Position> findMonsterCoordinates(std::optional<std::set<Position>> area = std::nullopt);
    std::tuple<Position, Direction> findPlayer();
    bool isPassable(int x, int y);
    bool isPassableInDirection(Position position, Direction fromDirection);
    int monsterCount(std::optional<std::set<Position>> area = std::nullopt);
    bool isConquered();
    void makeConquered();

private:
    Tiles tiles;
};

#endif // DRODBOT_ROOM_H