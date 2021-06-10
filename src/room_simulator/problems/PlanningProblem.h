#include <array>
#include <vector>
#include <set>
#include "../Room.h"
#include "../Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../ObjectiveReacher.h"

class PlanningProblem : public Problem<Room, Objective>
{
public:
    PlanningProblem(Room room, Objective objective);
    Room initialState();
    std::set<Objective> actions(Room state);
    Room result(Room state, Objective action);
    bool goalTest(Room state);
    int stepCost(Room state, Objective action, Room result);
    int heuristic(Room state);

private:
    Room room;
    Objective objective;
    ObjectiveReacher objectiveReacher;
    std::set<Objective> availableObjectives;
};