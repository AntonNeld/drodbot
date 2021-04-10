#include <map>
#include <set>
#include "AStarSearcher.h"
#include "Node.h"

template <class State, class SearchAction>
AStarSearcher<State, SearchAction>::AStarSearcher(Problem<State, SearchAction> *problem) : problem(problem){};

template <class State, class SearchAction>
std::vector<SearchAction> AStarSearcher<State, SearchAction>::findSolution()
{
    Node<State, SearchAction> startingNode = Node<State, SearchAction>(
        this->problem->initialState(), 0, NULL, NULL);
    if (this->problem.goalTest(startingNode.state))
    {
        return startingNode.getSolution();
    }

    bool priority = [](Node<State, SearchAction> a, Node<State, SearchAction> b) {
        // TODO: Heuristic
        // TODO: Correct order?
        return a.pathCost > b.pathCost;
    };
    std::set<Node<State, SearchAction>, decltype(priority)> frontier(priority);
    frontier.insert(startingNode);
    std::map<State, Node<State, SearchAction>> frontierByState;
    frontierByState.insert(std::pair<State, Node<State, SearchAction>>(startingNode.state, startingNode));
    std::set<State> explored;

    int iterations = 0;
    while (frontier.size() != 0)
    {
        Node<State, SearchAction> node = frontier.begin();
        frontier.erase(node);
        frontierByState.erase(node.state);
        if (this->problem->goalTest(node.state))
        {
            return node.solution();
        }
        explored.insert(node.state);
        std::set<SearchAction> actions = this->problem->actions(node.state);

        typename std::set<SearchAction>::iterator it;
        for (it = actions.begin(); it != actions.end(); ++it)
        {
            SearchAction action = *it;
            Node<State, SearchAction> child = node.getChild(this->problem, action);
            // If the frontier has a node with the same state, possibly replace it
            if (frontierByState.find(child.state) != frontierByState.end())
            {
                Node<State, SearchAction> otherNode = frontierByState.find(child.state);
                if (child.pathCost < otherNode.pathCost)
                {
                    frontier.erase(otherNode);
                    frontier.insert(child);
                    frontierByState.insert(std::pair<State, Node<State, SearchAction>>(child.state, child));
                }
            }
            // Else, add it to the frontier if it's not explored
            else if (explored.find(child.state) != explored.end())
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