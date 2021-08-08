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
    ObjectiveReacher(Room room);
    ~ObjectiveReacher();
    RoomPlayer *getRoomPlayer();
    Solution<DerivedRoom, Action> findSolution(DerivedRoom room, Objective objective);
    void start(DerivedRoom room, Objective objective);
    void nextPhase();
    ObjectiveReacherPhase getPhase();
    Solution<DerivedRoom, Action> getSolution();
    Searcher<Position, Action> *getPathfindingSearcher();
    Searcher<DerivedRoom, Action> *getRoomSimulationSearcher();

private:
    void preparePathfindingPhase();
    Solution<Position, Action> finishPathfindingPhase();
    void prepareSimulationPhase();
    Solution<DerivedRoom, Action> finishSimulationPhase();

    std::map<std::tuple<DerivedRoom, Objective>, Solution<DerivedRoom, Action>> cachedSolutions;
    RoomPlayer *roomPlayer;
    ObjectiveReacherPhase phase;
    std::optional<DerivedRoom> currentRoom;
    std::optional<Objective> currentObjective;
    std::optional<Solution<Position, Action>> pathfindingSolution;
    std::optional<Solution<DerivedRoom, Action>> solution;
    std::optional<PathfindingProblem *> pathfindingProblem;
    std::optional<Searcher<Position, Action> *> pathfindingSearcher;
    std::optional<DerivedRoomProblem *> roomProblem;
    std::optional<Searcher<DerivedRoom, Action> *> simulationSearcher;
};

#endif // DRODBOT_OBJECTIVEREACHER_H