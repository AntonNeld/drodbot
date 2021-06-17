#ifndef DRODBOT_OBJECTIVEREACHER_H
#define DRODBOT_OBJECTIVEREACHER_H

#include <tuple>
#include <vector>
#include <map>
#include <optional>
#include "typedefs.h"
#include "Room.h"
#include "objectives/Objective.h"
#include "problems/PathfindingProblem.h"
#include "problems/DerivedRoomProblem.h"
#include "search/Searcher.h"

enum class ObjectiveReacherPhase
{
    NOTHING,
    CHECK_CACHE,
    PATHFIND,
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
    Searcher<Position, Action> *getPathfindingSearcher();
    Searcher<DerivedRoom, Action> *getRoomSimulationSearcher();

private:
    void preparePathfindingPhase();
    Solution<Position, Action> finishPathfindingPhase();
    void prepareSimulationPhase(Solution<Position, Action> pathfindingSolution);
    Solution<DerivedRoom, Action> finishSimulationPhase();

    std::map<std::tuple<Room, Objective>, Solution<Room, Action>> cachedSolutions;
    ObjectiveReacherPhase phase;
    std::optional<Room> currentRoom;
    std::optional<Objective> currentObjective;
    std::optional<Solution<Room, Action>> solution;
    std::optional<PathfindingProblem *> pathfindingProblem;
    std::optional<Searcher<Position, Action> *> pathfindingSearcher;
    std::optional<DerivedRoomProblem *> roomProblem;
    std::optional<Searcher<DerivedRoom, Action> *> simulationSearcher;
    bool claimedRoomPlayer;
};

#endif // DRODBOT_OBJECTIVEREACHER_H