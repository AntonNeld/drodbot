#include "Node.h"

template <class State, class SearchAction>
Node<State, SearchAction>::Node(State state,
                                int pathCost,
                                SearchAction action,
                                Node *parent) : state(state),
                                                pathCost(pathCost),
                                                action(action),
                                                parent(parent)
{
}

template <class State, class SearchAction>
Node<State, SearchAction> Node<State, SearchAction>::getChild(Problem<State, SearchAction> *problem, SearchAction action)
{
    State result = problem->result(this->state, action);
    return Node<State, SearchAction>(result, this->pathCost + 1, action, this);
}

template <class State, class SearchAction>
std::vector<SearchAction> getSolution()
{
    if (this->parent == NULL)
    {
        return {}
    }
    std::vector<SearchAction> actions = this->parent.getSolution();
    actions.push_back(this->action);
    return actions;
}