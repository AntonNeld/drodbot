#ifndef DRODBOT_SEARCH_PROBLEM_H
#define DRODBOT_SEARCH_PROBLEM_H

#include <set>

template <class State, class SearchAction>
class Problem
{
public:
    virtual State initialState();
    virtual std::set<SearchAction> actions(State);
    virtual State result(State, SearchAction);
    virtual bool goalTest(State);
    virtual int stepCost(State, SearchAction, State);
    virtual int heuristic(State);
};

#endif // DRODBOT_SEARCH_PROBLEM_H