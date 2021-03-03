#ifndef DRODBOT_TYPEDEFS_H
#define DRODBOT_TYPEDEFS_H

#include <array>
#include <tuple>
#include <vector>

// An action the player can take. The values need to match the ones in common.py.
enum class Action
{
    SW = 1,
    S = 2,
    SE = 3,
    W = 4,
    WAIT = 5,
    E = 6,
    NW = 7,
    N = 8,
    NE = 9,
    CW = 10,
    CCW = 11,
};

// A type of element.
enum class ElementType
{
    UNKNOWN,
    NOTHING,
    WALL,
    PIT,
    MASTER_WALL,
    YELLOW_DOOR,
    YELLOW_DOOR_OPEN,
    GREEN_DOOR,
    GREEN_DOOR_OPEN,
    BLUE_DOOR,
    BLUE_DOOR_OPEN,
    STAIRS,
    FORCE_ARROW,
    CHECKPOINT,
    ORB,
    SCROLL,
    OBSTACLE,
    BEETHRO,
    BEETHRO_SWORD,
    ROACH,
    CONQUER_TOKEN,
    FLOOR,
};

// A direction an element can have. Not all elements can have all directions,
// but this is not enforced.
enum class Direction
{
    NONE,
    N,
    NE,
    E,
    SE,
    S,
    SW,
    W,
    NW,
};

enum class OrbEffect
{
    OPEN,
    CLOSE,
    TOGGLE,
};

typedef std::vector<std::tuple<int, int, OrbEffect>> OrbEffects; // x, y, effect

// An element in a room.
struct Element
{
    Element(ElementType type = ElementType::NOTHING, Direction direction = Direction::NONE, OrbEffects orbEffects = {}) : type(type), direction(direction), orbEffects(orbEffects) {}
    ElementType type = ElementType::NOTHING;
    Direction direction = Direction::NONE;
    OrbEffects orbEffects = {}; // Only actually used for orbs
};

// The contents of a tile. TODO: Enforce correct element types in each layer.
struct Tile
{
    Element roomPiece = Element();
    Element floorControl = Element();
    Element checkpoint = Element();
    Element item = Element();
    Element monster = Element();
};
// A column in a room.
typedef std::array<Tile, 32> Column;

// A representation of a room that can be imported/exported from/to Python code.
typedef std::array<Column, 38> Room;

#endif // DRODBOT_TYPEDEFS_H