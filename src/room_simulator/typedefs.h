#ifndef DRODBOT_TYPEDEFS_H
#define DRODBOT_TYPEDEFS_H

#include <array>
#include <tuple>
#include <vector>
#include <set>

typedef std::tuple<int, int> Position;

// An action the player can take. The values need to match the ones in common.py.
enum class Action
{
    SW,
    S,
    SE,
    W,
    WAIT,
    E,
    NW,
    N,
    NE,
    CW,
    CCW,
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
    bool operator==(const Element otherElement) const
    {
        return this->type == otherElement.type &&
               this->direction == otherElement.direction &&
               this->orbEffects == otherElement.orbEffects;
    };
    bool operator<(const Element otherElement) const
    {
        return this->type < otherElement.type ||
               this->direction < otherElement.direction ||
               this->orbEffects < otherElement.orbEffects;
    };
};

// The contents of a tile. TODO: Enforce correct element types in each layer.
struct Tile
{
    Tile(
        Element roomPiece = Element(),
        Element floorControl = Element(),
        Element checkpoint = Element(),
        Element item = Element(),
        Element monster = Element()) : roomPiece(roomPiece),
                                       floorControl(floorControl),
                                       checkpoint(checkpoint),
                                       item(item),
                                       monster(monster)
    {
    }
    Element roomPiece = Element();
    Element floorControl = Element();
    Element checkpoint = Element();
    Element item = Element();
    Element monster = Element();
    bool operator==(const Tile otherTile) const
    {
        return this->roomPiece == otherTile.roomPiece &&
               this->floorControl == otherTile.floorControl &&
               this->checkpoint == otherTile.checkpoint &&
               this->item == otherTile.item &&
               this->monster == otherTile.monster;
    };
    bool operator<(const Tile otherTile) const
    {
        return this->roomPiece < otherTile.roomPiece ||
               this->floorControl < otherTile.floorControl ||
               this->checkpoint < otherTile.checkpoint ||
               this->item < otherTile.item ||
               this->monster < otherTile.monster;
    };
};

// TODO: Make something more extensible
struct Objective
{
    Objective(
        // If true, objective is reached if the sword is at any of the tiles,
        // if false, objective is reached if Beethro is at any of the tiles
        bool swordAtTile,
        std::set<Position> tiles) : swordAtTile(swordAtTile), tiles(tiles)
    {
    }
    bool operator<(const Objective &other) const
    {
        if (this->swordAtTile != other.swordAtTile)
        {
            return this->swordAtTile;
        }
        if (this->tiles.size() != other.tiles.size())
        {
            return this->tiles.size() < other.tiles.size();
        }
        auto thisTilesIterator = this->tiles.begin();
        auto otherTilesIterator = other.tiles.begin();
        while (thisTilesIterator != this->tiles.end())
        {
            if (*thisTilesIterator != *otherTilesIterator)
            {
                return *thisTilesIterator < *otherTilesIterator;
            }
            ++thisTilesIterator;
            ++otherTilesIterator;
        }
        return false;
    };
    bool swordAtTile;
    std::set<Position> tiles;
};

enum class FailureReason
{
    NO_FAILURE,
    ITERATION_LIMIT_REACHED,
    EXHAUSTED_FRONTIER,
};

template <class SearchAction>
struct Solution
{
    Solution(bool exists,
             std::vector<SearchAction> actions,
             FailureReason failureReason = FailureReason::NO_FAILURE) : exists(exists),
                                                                        actions(actions),
                                                                        failureReason(failureReason){};
    bool exists;
    std::vector<SearchAction> actions;
    FailureReason failureReason;
};

#endif // DRODBOT_TYPEDEFS_H