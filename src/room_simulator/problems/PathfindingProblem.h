#ifndef DRODBOT_PATHFINDINGPROBLEM_H
#define DRODBOT_PATHFINDINGPROBLEM_H

#include <array>
#include <vector>
#include <set>
#include "../Room.h"
#include "../typedefs.h"
#include "../search/Problem.h"

class PathfindingProblem final : public Problem<Position, Action>
{
public:
    PathfindingProblem(Position startPosition, Room room, std::set<Position> goals);
    Position initialState();
    std::set<Action> actions(Position state);
    Position result(Position state, Action action);
    bool goalTest(Position state);
    int stepCost(Position state, Action action, Position result);
    int heuristic(Position state);

private:
    Position startPosition;
    Room room;
    std::set<Position> goals;
};

#endif // DRODBOT_PATHFINDINGPROBLEM_H