#include <set>
#include <stdlib.h>
#include "../Room.h"
#include "../objectives/Objective.h"
#include "../ObjectiveReacher.h"
#include "../typedefs.h"
#include "PlanningProblem.h"
#include "../objectives/StabObjective.h"
#include "../objectives/MonsterCountObjective.h"
#include "../utils.h"

std::vector<std::set<Position>> findAreas(Room room)
{
    std::vector<std::set<Position>> areas = {};
    std::vector<Position> floors = room.findCoordinates(ElementType::FLOOR);
    std::set<Position> toCheck = {};
    toCheck.insert(floors.begin(), floors.end());
    while (!toCheck.empty())
    {
        std::set<Position> area = floodFill(*toCheck.begin(), room, true, true, false, true, false);
        areas.push_back(area);
        for (auto it = area.begin(); it != area.end(); ++it)
        {
            toCheck.erase(*it);
        }
    }
    return areas;
}

PlanningProblem::PlanningProblem(Room room,
                                 Objective objective,
                                 ObjectiveReacher *objectiveReacher) : room(room),
                                                                       objective(objective),
                                                                       objectiveReacher(objectiveReacher),
                                                                       orbs(room.findCoordinates(ElementType::ORB)),
                                                                       areas(findAreas(room))
{
}

Room PlanningProblem::initialState()
{
    return this->room;
}

std::set<Objective> PlanningProblem::actions(Room state)
{
    std::set<Objective> objectives = {};
    // Always try reaching the final objective
    // TODO: May not make sense if it's something like clearing the room
    objectives.insert(this->objective);
    // Try to strike each orb
    for (auto it = this->orbs.begin(); it != this->orbs.end(); ++it)
    {
        objectives.insert(StabObjective({*it}));
    }
    // Go to an area
    for (auto it = areas.begin(); it != areas.end(); ++it)
    {
        ReachObjective objective = ReachObjective(*it);
        objectives.insert(objective);
    }
    // Kill a monster
    MonsterCountObjective killSomething = MonsterCountObjective(room.monsterCount() - 1);
    objectives.insert(killSomething);
    // Only return objectives we can actually reach
    std::set<Objective> reachableObjectives = {};
    for (auto it = objectives.begin(); it != objectives.end(); ++it)
    {
        Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, *it);
        if (solution.exists)
        {
            reachableObjectives.insert(*it);
        }
    }
    return reachableObjectives;
}

Room PlanningProblem::result(Room state, Objective action)
{
    Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.finalState.value();
}

bool PlanningProblem::goalTest(Room state)
{
    return objectiveFulfilled(this->objective, state);
}

int PlanningProblem::stepCost(Room state, Objective action, Room result)
{
    Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, action);
    return solution.actions.value().size();
}

int PlanningProblem::heuristic(Room state)
{
    return 0;
}