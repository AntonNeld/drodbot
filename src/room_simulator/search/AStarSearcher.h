#ifndef DRODBOT_SEARCH_ASTARSEARCHER_H
#define DRODBOT_SEARCH_ASTARSEARCHER_H

#include <iostream>
#include <vector>
#include <map>
#include <set>
#include "Problem.h"
#include "Node.h"

template <class State, class SearchAction>
class AStarSearcher
{
public:
    AStarSearcher(Problem<State, SearchAction> *problem, int iterationLimit = 10000);
    std::vector<SearchAction> findSolution();
    // Below methods are intended for inspecting the algorithm.
    // findSolution() should be enough for real usage.
    void expandNextNode();
    int getIterations();
    std::vector<SearchAction> getCurrentPath();
    State getCurrentState();
    int getCurrentStateHeuristic();
    std::set<State> getFrontierStates();
    std::set<State> getExplored();
    bool foundSolution();

private:
    void popNextNode();
    void expandCurrentNode();
    Problem<State, SearchAction> *problem;
    // The frontier is the next nodes that will be executed. It's sorted so the
    // lowest-cost node is first. Using a multiset as a sorted list here, which
    // works because we overload < in Node.
    std::multiset<Node<State, SearchAction>> frontier;
    // This is so we can easily check whether a node with a certain state is in
    // the frontier. This is used to replace a node if a lower-cost node with the
    // same state is found later.
    std::map<State, Node<State, SearchAction>> frontierByState;
    // The current node being expanded
    Node<State, SearchAction> currentNode;
    // This contains all explored nodes, to avoid exploring them again.
    std::set<State> explored;
    // The number of iterations, so we can stop at some reasonable limit if it
    // turns out the problem is intractable.
    int iterations;
    // The iteration limit, after which we will throw an exception
    int iterationLimit;
};

template <class State, class SearchAction>
inline AStarSearcher<State, SearchAction>::AStarSearcher(
    Problem<State, SearchAction> *problem,
    int iterationLimit) : problem(problem),
                          frontier({}),
                          frontierByState({}),
                          currentNode(Node<State, SearchAction>(problem)),
                          explored({problem->initialState()}),
                          iterations(0),
                          iterationLimit(iterationLimit)
{
    // We've already initialized the member variables as if we've popped the
    // first node from the frontier.
    this->expandCurrentNode();
};

template <class State, class SearchAction>
inline void AStarSearcher<State, SearchAction>::expandNextNode()
{
    this->popNextNode();
    this->expandCurrentNode();
};

template <class State, class SearchAction>
inline void AStarSearcher<State, SearchAction>::popNextNode()
{
    // If the frontier is empty, we've already tried all states we can reach
    if (this->frontier.size() == 0)
    {
        throw std::runtime_error("No solution");
    }
    // Pop the lowest-cost node from the frontier and make it the current node
    typename std::multiset<Node<State, SearchAction>>::iterator nodeIterator = this->frontier.begin();
    this->currentNode = *nodeIterator;
    this->frontier.erase(nodeIterator);
    this->frontierByState.erase(this->currentNode.state);
    this->explored.insert(this->currentNode.state);
    this->iterations += 1;
}

template <class State, class SearchAction>
inline void AStarSearcher<State, SearchAction>::expandCurrentNode()
{
    // Expand the current node and add its children to the frontier where appropriate
    std::set<SearchAction> actions = this->problem->actions(this->currentNode.state);
    typename std::set<SearchAction>::iterator actionIterator;
    for (actionIterator = actions.begin(); actionIterator != actions.end(); ++actionIterator)
    {
        SearchAction action = *actionIterator;
        Node<State, SearchAction> childNode = this->currentNode.getChild(action);
        // If the frontier has a node with the same state, replace it if its path cost is higher
        if (this->frontierByState.find(childNode.state) != this->frontierByState.end())
        {
            Node<State, SearchAction> otherNode = std::get<1>(*(this->frontierByState.find(childNode.state)));
            if (childNode.pathCost < otherNode.pathCost)
            {
                // Find the actual other node in the frontier and replace it. We
                // narrow it down to the nodes which the multiset considers to be
                // equivalent to the one from frontierByState, i.e. all nodes
                // with the same path cost.
                std::pair<typename std::multiset<Node<State, SearchAction>>::iterator,
                          typename std::multiset<Node<State, SearchAction>>::iterator>
                    range = this->frontier.equal_range(otherNode);
                typename std::multiset<Node<State, SearchAction>>::iterator it;
                for (it = std::get<0>(range); it != std::get<1>(range); ++it)
                {
                    if (it->state == childNode.state)
                    {
                        frontier.erase(it);
                        break;
                    }
                }
                this->frontier.insert(childNode);
                this->frontierByState.insert(std::pair<State, Node<State, SearchAction>>(childNode.state, childNode));
            }
        }
        // If it's not already in the frontier, add it if it's not explored
        else if (explored.find(childNode.state) == this->explored.end())
        {
            this->frontier.insert(childNode);
            this->frontierByState.insert(std::pair<State, Node<State, SearchAction>>(childNode.state, childNode));
        }
    }
}

template <class State, class SearchAction>
inline int AStarSearcher<State, SearchAction>::getIterations()
{
    return this->iterations;
}

template <class State, class SearchAction>
inline std::vector<SearchAction> AStarSearcher<State, SearchAction>::getCurrentPath()
{
    return this->currentNode.actions;
}

template <class State, class SearchAction>
inline State AStarSearcher<State, SearchAction>::getCurrentState()
{
    return this->currentNode.state;
}

template <class State, class SearchAction>
inline int AStarSearcher<State, SearchAction>::getCurrentStateHeuristic()
{
    return this->problem->heuristic(this->currentNode.state);
}

template <class State, class SearchAction>
inline std::set<State> AStarSearcher<State, SearchAction>::getFrontierStates()
{
    std::set<State> frontierStates = {};
    typename std::multiset<Node<State, SearchAction>>::iterator iterator;
    for (iterator = this->frontier.begin(); iterator != this->frontier.end(); ++iterator)
    {
        frontierStates.insert(iterator->state);
    }
    return frontierStates;
}

template <class State, class SearchAction>
inline std::set<State> AStarSearcher<State, SearchAction>::getExplored()
{
    return this->explored;
}

template <class State, class SearchAction>
inline bool AStarSearcher<State, SearchAction>::foundSolution()
{
    return this->problem->goalTest(this->currentNode.state);
}

template <class State, class SearchAction>
inline std::vector<SearchAction> AStarSearcher<State, SearchAction>::findSolution()
{
    while (!this->foundSolution())
    {
        if (this->iterations > this->iterationLimit)
        {
            throw std::runtime_error("Too many iterations");
        }
        this->expandNextNode();
    }
    return this->currentNode.actions;
};
#endif // DRODBOT_SEARCH_ASTARSEARCHER_H