#ifndef DRODBOT_SEARCH_NODE_H
#define DRODBOT_SEARCH_NODE_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Node
{
public:
    Node(State state, int pathCost, SearchAction action, Node *parent);
    Node getChild(Problem *problem, SearchAction action);
    std::vector<SearchAction> getSolution();

private:
    State state;
    int pathCost;
    SearchAction action;
    Node *parent;
};

#endif // DRODBOT_SEARCH_NODE_H