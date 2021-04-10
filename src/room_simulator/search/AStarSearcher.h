#ifndef DRODBOT_SEARCH_ASTARSEARCHER_H
#define DRODBOT_SEARCH_ASTARSEARCHER_H

#include <vector>
#include <map>
#include <set>
#include "Problem.h"
#include "Node.h"

template <class State, class SearchAction>
class AStarSearcher
{
public:
    // TODO: Heuristic
    AStarSearcher(Problem<State, SearchAction> *problem);
    std::vector<SearchAction> findSolution();

private:
    Problem<State, SearchAction> *problem;
};

template <class State, class SearchAction>
inline AStarSearcher<State, SearchAction>::AStarSearcher(Problem<State, SearchAction> *problem) : problem(problem){};

template <class State, class SearchAction>
inline std::vector<SearchAction> AStarSearcher<State, SearchAction>::findSolution()
{
    Node<State, SearchAction> startingNode = Node<State, SearchAction>(this->problem->initialState());
    if (this->problem->goalTest(startingNode.state))
    {
        return startingNode.actions;
    }

    // Using a multiset as a sorted list here. This works because we overload < in Node.
    std::multiset<Node<State, SearchAction>> frontier;
    frontier.insert(startingNode);

    std::map<State, Node<State, SearchAction>> frontierByState;
    frontierByState.insert(std::pair<State, Node<State, SearchAction>>(startingNode.state, startingNode));
    std::set<State> explored;

    int iterations = 0;
    while (frontier.size() != 0)
    {
        typename std::multiset<Node<State, SearchAction>>::iterator nodeIterator = frontier.begin();
        Node<State, SearchAction> node = *nodeIterator;
        frontier.erase(nodeIterator);
        frontierByState.erase(node.state);
        if (this->problem->goalTest(node.state))
        {
            return node.actions;
        }
        explored.insert(node.state);
        std::set<SearchAction> actions = this->problem->actions(node.state);

        typename std::set<SearchAction>::iterator actionIterator;
        for (actionIterator = actions.begin(); actionIterator != actions.end(); ++actionIterator)
        {
            SearchAction action = *actionIterator;
            Node<State, SearchAction> child = node.getChild(this->problem, action);
            // If the frontier has a node with the same state, possibly replace it
            if (frontierByState.find(child.state) != frontierByState.end())
            {
                Node<State, SearchAction> otherNode = std::get<1>(*frontierByState.find(child.state));
                if (child.pathCost < otherNode.pathCost)
                {
                    // Find the actual other node in the frontier and replace it
                    std::pair<typename std::multiset<Node<State, SearchAction>>::iterator,
                              typename std::multiset<Node<State, SearchAction>>::iterator>
                        range = frontier.equal_range(otherNode);
                    typename std::multiset<Node<State, SearchAction>>::iterator it;
                    for (it = std::get<0>(range); it != std::get<1>(range); ++it)
                    {
                        if (it->state == otherNode.state)
                        {
                            frontier.erase(it);
                            break;
                        }
                    }
                    frontier.insert(child);
                    frontierByState.insert(std::pair<State, Node<State, SearchAction>>(child.state, child));
                }
            }
            // Else, add it to the frontier if it's not explored
            else if (explored.find(child.state) == explored.end())
            {
                frontier.insert(child);
                frontierByState.insert(std::pair<State, Node<State, SearchAction>>(child.state, child));
            }
        }
        iterations += 1;
        // TODO: Define iteration limit somewhere else
        if (iterations > 10000)
        {
            throw std::runtime_error("Too many iterations");
        }
    }
    throw std::runtime_error("No solution");
};
#endif // DRODBOT_SEARCH_ASTARSEARCHER_H