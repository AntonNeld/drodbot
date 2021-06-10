#include <vector>
#include <map>
#include <tuple>
#include "ObjectiveReacher.h"
#include "Objective.h"
#include "typedefs.h"
#include "search/Searcher.h"
#include "problems/RoomProblem.h"

ObjectiveReacher::ObjectiveReacher() : cachedSolutions({}){};

Solution<Action> ObjectiveReacher::findSolution(Room room, Objective objective)
{
    // Return solution from the cache if it exists
    auto foundSolution = this->cachedSolutions.find({room, objective});
    if (foundSolution != this->cachedSolutions.end())
    {
        return std::get<1>(*foundSolution);
    }
    // Else, try to find the solution
    RoomProblem problem = RoomProblem(room, objective);
    // Low iteration limit for now, to avoid finding the solution indirectly by accident
    Searcher<Room, Action> searcher = Searcher<Room, Action>(&problem, true, true, false, 100);
    Solution<Action> solution = searcher.findSolution();
    this->cachedSolutions.insert({{room, objective}, solution});
    return solution;
};