#ifndef DRODBOT_TYPEDEFS_H
#define DRODBOT_TYPEDEFS_H

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

#endif // DRODBOT_TYPEDEFS_H