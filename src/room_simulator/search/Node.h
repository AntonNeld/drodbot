#ifndef DRODBOT_SEARCH_NODE_H
#define DRODBOT_SEARCH_NODE_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Node
{
public:
    Node(Problem<State, SearchAction> *problem, State state, int pathCost, std::vector<SearchAction> actions, int priority);
    Node(Problem<State, SearchAction> *problem); // Starting node
    bool operator<(const Node &otherNode) const { return this->priority < otherNode.priority; }
    Problem<State, SearchAction> *problem;
    State state;
    int pathCost;
    std::vector<SearchAction> actions;
    int priority;
};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(Problem<State, SearchAction> *problem,
                                       State state,
                                       int pathCost,
                                       std::vector<SearchAction> actions,
                                       int priority) : problem(problem),
                                                       state(state),
                                                       pathCost(pathCost),
                                                       actions(actions),
                                                       priority(priority){};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(Problem<State, SearchAction> *problem) : problem(problem),
                                                                                state(problem->initialState()),
                                                                                pathCost(0),
                                                                                actions({}),
                                                                                priority(problem->heuristic(state)){};

#endif // DRODBOT_SEARCH_NODE_H