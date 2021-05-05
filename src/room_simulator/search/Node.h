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
    Node getChild(SearchAction action);
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

template <class State, class SearchAction>
inline Node<State, SearchAction> Node<State, SearchAction>::getChild(SearchAction action)
{
    State result = this->problem->result(this->state, action);
    std::vector<SearchAction> childActions = this->actions;
    childActions.push_back(action);
    int priority = this->pathCost + 1 + this->problem->heuristic(result);
    return Node<State, SearchAction>(this->problem, result, this->pathCost + 1, childActions, priority);
}

#endif // DRODBOT_SEARCH_NODE_H