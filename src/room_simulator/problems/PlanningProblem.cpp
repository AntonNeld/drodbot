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
    for (auto it = areas.begin(); it != areas.end(); ++it)
    {
        // We are only interested in areas with monsters for now
        if (room.monsterCount(*it) > 0)
        {
            // Go to an area
            ReachObjective goObjective = ReachObjective(*it);
            objectives.insert(goObjective);
            // Clear an area
            MonsterCountObjective killObjective = MonsterCountObjective(0, false, *it);
            objectives.insert(killObjective);
        }
    }
    // We may be far from a monster, so add an objective to either:
    // - Stab any tile which currently has a monster (to get pathfinding)
    // - Kill a monster (to stop going to the tile if we kill it early)
    std::vector<Position> monsterPositions = state.findMonsterCoordinates();
    std::set<Position> monsterPositionsSet = {};
    monsterPositionsSet.insert(monsterPositions.begin(), monsterPositions.end());
    objectives.insert(OrObjective({StabObjective(monsterPositionsSet),
                                   MonsterCountObjective(monsterPositions.size() - 1)}));
    // Only return objectives we can actually reach, but haven't reached already
    std::set<Objective> reachableObjectives = {};
    for (auto it = objectives.begin(); it != objectives.end(); ++it)
    {
        if (!objectiveFulfilled(*it, state))
        {
            Solution<Room, Action> solution = this->objectiveReacher->findSolution(state, *it);
            if (solution.exists)
            {
                reachableObjectives.insert(*it);
            }
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
    return objectiveHeuristic(this->objective, state);
}