#include <vector>
#include <set>
#include "Room.h"
#include "typedefs.h"
#include "search/AStarSearcher.h"
#include "problems/PathfindingProblem.h"

std::vector<Action> findPath(Position start, std::set<Position> goals, Room room)
{
    // TODO: Implement pre-check?
    PathfindingProblem problem = PathfindingProblem(start, room, goals);
    AStarSearcher<Position, Action> searcher = AStarSearcher<Position, Action>(&problem);
    return searcher.findSolution();
}
