#ifndef DRODBOT_SEARCH_NODE_H
#define DRODBOT_SEARCH_NODE_H

#include <vector>
#include "Problem.h"

template <class State, class SearchAction>
class Node
{
public:
    Node(Problem<State, SearchAction> *problem, State state, int pathCost, std::vector<SearchAction> actions);
    Node(Problem<State, SearchAction> *problem); // Starting node
    bool operator<(const Node &otherNode) const { return this->pathCost < otherNode.pathCost; }
    Node getChild(SearchAction action);
    std::vector<SearchAction> getSolution();
    Problem<State, SearchAction> *problem;
    State state;
    int pathCost;
    std::vector<SearchAction> actions;
};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(Problem<State, SearchAction> *problem,
                                       State state,
                                       int pathCost,
                                       std::vector<SearchAction> actions) : problem(problem),
                                                                            state(state),
                                                                            pathCost(pathCost),
                                                                            actions(actions){};

template <class State, class SearchAction>
inline Node<State, SearchAction>::Node(Problem<State, SearchAction> *problem) : problem(problem),
                                                                                state(problem->initialState()),
                                                                                pathCost(0),
                                                                                actions({}){};

template <class State, class SearchAction>
inline Node<State, SearchAction> Node<State, SearchAction>::getChild(SearchAction action)
{
    State result = this->problem->result(this->state, action);
    std::vector<SearchAction> childActions = this->actions;
    childActions.push_back(action);
    return Node<State, SearchAction>(this->problem, result, this->pathCost + 1, childActions);
}

#endif // DRODBOT_SEARCH_NODE_H