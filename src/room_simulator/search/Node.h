#ifndef DRODBOT_SEARCH_NODE_H
#define DRODBOT_SEARCH_NODE_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Node
{
public:
    Node(State state, int pathCost, SearchAction action, Node *parent);
    Node(State state); // Starting node
    bool operator<(const Node &otherNode) const { return this->pathCost < otherNode.pathCost; }
    Node getChild(Problem<State, SearchAction> *problem, SearchAction action);
    std::vector<SearchAction> getSolution();
    State state;
    int pathCost;

private:
    SearchAction action;
    Node *parent;
};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(State state,
                                       int pathCost,
                                       SearchAction action,
                                       Node *parent) : state(state),
                                                       pathCost(pathCost),
                                                       action(action),
                                                       parent(parent){};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(State state) : state(state)
{
    this->pathCost = 0;
    // Leave this->action uninitialized, we will not use it
    this->parent = NULL;
};

template <class State, class SearchAction>
inline Node<State, SearchAction> Node<State, SearchAction>::getChild(Problem<State, SearchAction> *problem, SearchAction action)
{
    State result = problem->result(this->state, action);
    return Node<State, SearchAction>(result, this->pathCost + 1, action, this);
}

template <class State, class SearchAction>
inline std::vector<SearchAction> Node<State, SearchAction>::getSolution()
{
    if (this->parent == NULL)
    {
        return {};
    }
    std::vector<SearchAction> actions = this->parent->getSolution();
    actions.push_back(this->action);
    return actions;
}

#endif // DRODBOT_SEARCH_NODE_H