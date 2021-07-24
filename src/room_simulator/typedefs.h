#ifndef DRODBOT_TYPEDEFS_H
#define DRODBOT_TYPEDEFS_H

#include <array>
#include <tuple>
#include <vector>
#include <set>
#include <optional>

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
    RED_DOOR,
    RED_DOOR_OPEN,
    TRAPDOOR,
    STAIRS,
    FORCE_ARROW,
    CHECKPOINT,
    ORB,
    MIMIC_POTION,
    INVISIBILITY_POTION,
    SCROLL,
    OBSTACLE,
    BEETHRO,
    BEETHRO_SWORD,
    ROACH,
    ROACH_QUEEN,
    EVIL_EYE,
    EVIL_EYE_AWAKE,
    WRAITHWING,
    SPIDER,
    GOBLIN,
    BRAIN,
    TAR_BABY,
    MIMIC,
    MIMIC_SWORD,
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
    Element(ElementType type = ElementType::NOTHING,
            Direction direction = Direction::NONE,
            OrbEffects orbEffects = {},
            std::optional<int> turnOrder = std::nullopt) : type(type),
                                                           direction(direction),
                                                           orbEffects(orbEffects),
                                                           turnOrder(turnOrder){};
    ElementType type = ElementType::NOTHING;
    Direction direction = Direction::NONE;
    OrbEffects orbEffects = {};   // Only actually used for orbs
    std::optional<int> turnOrder; // Where a monster is in the turn order, 0-indexed.
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

enum class FailureReason
{
    NO_FAILURE,
    FAILED_PRECHECK,
    ITERATION_LIMIT_REACHED,
    EXHAUSTED_FRONTIER,
};

template <class State, class SearchAction>
struct Solution
{
    Solution(bool exists,
             std::optional<std::vector<SearchAction>> actions,
             std::optional<State> finalState,
             FailureReason failureReason = FailureReason::NO_FAILURE) : exists(exists),
                                                                        actions(actions),
                                                                        finalState(finalState),
                                                                        failureReason(failureReason){};
    bool exists;
    std::optional<std::vector<SearchAction>> actions;
    std::optional<State> finalState;
    FailureReason failureReason;
};

#endif // DRODBOT_TYPEDEFS_H