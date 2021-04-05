#ifndef DRODBOT_SEARCH_PROBLEM_H
#define DRODBOT_SEARCH_PROBLEM_H

#include <vector>

template <class State, class SearchAction>
struct Problem
{
public:
    State (*initialState)();
    std::vector<SearchAction> (*actions)(State);
    State (*result)(State, SearchAction);
    bool (*goalTest)(State);
    int (*stepCost)(State, SearchAction, State);
};

#endif // DRODBOT_SEARCH_PROBLEM_H