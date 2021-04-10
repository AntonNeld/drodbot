#ifndef DRODBOT_SEARCH_NODE_H
#define DRODBOT_SEARCH_NODE_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Node
{
public:
    Node(State state, int pathCost, std::vector<SearchAction> actions);
    Node(State state); // Starting node
    bool operator<(const Node &otherNode) const { return this->pathCost < otherNode.pathCost; }
    Node getChild(Problem<State, SearchAction> *problem, SearchAction action);
    std::vector<SearchAction> getSolution();
    State state;
    int pathCost;
    std::vector<SearchAction> actions;
};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(State state,
                                       int pathCost,
                                       std::vector<SearchAction> actions) : state(state),
                                                                            pathCost(pathCost),
                                                                            actions(actions){};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(State state) : state(state)
{
    this->pathCost = 0;
    this->actions = {};
};

template <class State, class SearchAction>
inline Node<State, SearchAction> Node<State, SearchAction>::getChild(Problem<State, SearchAction> *problem, SearchAction action)
{
    State result = problem->result(this->state, action);
    std::vector<SearchAction> childActions = this->actions;
    childActions.push_back(action);
    return Node<State, SearchAction>(result, this->pathCost + 1, childActions);
}

#endif // DRODBOT_SEARCH_NODE_H