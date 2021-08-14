#ifndef DRODBOT_PLANNINGPROBLEM_H
#define DRODBOT_PLANNINGPROBLEM_H

#include <array>
#include <vector>
#include <set>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../ObjectiveReacher.h"

class PlanningProblem final : public Problem<DerivedRoom, Objective>
{
public:
    PlanningProblem(Objective objective, ObjectiveReacher *objectiveReacher);
    DerivedRoom initialState();
    std::vector<Objective> actions(DerivedRoom state);
    DerivedRoom result(DerivedRoom state, Objective action);
    bool goalTest(DerivedRoom state);
    int stepCost(DerivedRoom state, Objective action, DerivedRoom result);
    int heuristic(DerivedRoom state);

private:
    Objective objective;
    ObjectiveReacher *objectiveReacher;
    std::vector<Position> orbs;
};

#endif // DRODBOT_PLANNINGPROBLEM_H