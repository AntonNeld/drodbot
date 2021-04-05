#ifndef DRODBOT_SEARCH_PROBLEM_H
#define DRODBOT_SEARCH_PROBLEM_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Problem
{
public:
    virtual State initialState();
    virtual std::vector<SearchAction> actions(State state);
    virtual State result(State state, SearchAction action);
    virtual bool goalTest(State state);
    virtual int stepCost(State state, SearchAction action, State result);
};

#endif // DRODBOT_SEARCH_PROBLEM_H