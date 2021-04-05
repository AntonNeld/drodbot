#ifndef DRODBOT_SEARCH_ASTARSEARCHER_H
#define DRODBOT_SEARCH_ASTARSEARCHER_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class AStarSearcher
{
public:
    // TODO: Heuristic
    AStarSearcher(Problem *problem);
    std::vector<SearchAction> findSolution();
};

#endif // DRODBOT_SEARCH_ASTARSEARCHER_H