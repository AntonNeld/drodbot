#ifndef DRODBOT_OBJECTIVE_H
#define DRODBOT_OBJECTIVE_H

#include <set>
#include "typedefs.h"

// TODO: Make something more extensible
class Objective
{
public:
    Objective(
        bool swordAtTile,
        std::set<Position> tiles);
    bool operator<(const Objective) const;

    // If true, objective is reached if the sword is at any of the tiles,
    // if false, objective is reached if Beethro is at any of the tiles
    bool swordAtTile;
    std::set<Position> tiles;
};

#endif // DRODBOT_OBJECTIVE_H