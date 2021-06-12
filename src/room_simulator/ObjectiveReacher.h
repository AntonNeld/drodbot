#ifndef DRODBOT_OBJECTIVEREACHER_H
#define DRODBOT_OBJECTIVEREACHER_H

#include <tuple>
#include <vector>
#include <map>
#include <optional>
#include "typedefs.h"
#include "Room.h"
#include "Objective.h"
#include "problems/RoomProblem.h"
#include "search/Searcher.h"

enum class ObjectiveReacherPhase
{
    NOTHING,
    CHECK_CACHE,
    SIMULATE_ROOM,
    FINISHED,
};

class ObjectiveReacher
{
public:
    ObjectiveReacher();
    ~ObjectiveReacher();
    Solution<Room, Action> findSolution(Room room, Objective objective);
    void start(Room room, Objective objective);
    void nextPhase();
    ObjectiveReacherPhase getPhase();
    Solution<Room, Action> getSolution();
    Searcher<Room, Action> getRoomSimulationSearcher();

private:
    std::map<std::tuple<Room, Objective>, Solution<Room, Action>> cachedSolutions;
    ObjectiveReacherPhase phase;
    std::optional<Room> currentRoom;
    std::optional<Objective> currentObjective;
    std::optional<Solution<Room, Action>> solution;
    std::optional<RoomProblem *> roomProblem;
    std::optional<Searcher<Room, Action>> simulationSearcher;
};

#endif // DRODBOT_OBJECTIVEREACHER_H