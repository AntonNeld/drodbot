#ifndef DRODBOT_ROOM_H
#define DRODBOT_ROOM_H

#include <array>
#include <tuple>
#include "typedefs.h"

typedef std::array<Tile, 32> Column;
typedef std::array<Column, 38> Tiles;
typedef std::tuple<int, int> Position;
class Room
{
public:
    Room(Tiles tiles);
    Room copy();
    Tile getTile(Position position);
    void setTile(Position position, Tile tile);

private:
    Tiles tiles;
};

#endif // DRODBOT_ROOM_H