#include <vector>
#include <map>
#include <tuple>
#include <optional>
#include <set>
#include "RoomPlayer.h"
#include "ObjectiveReacher.h"
#include "objectives/Objective.h"
#include "typedefs.h"
#include "search/Searcher.h"
#include "problems/DerivedRoomProblem.h"
#include "utils.h"

ObjectiveReacher::ObjectiveReacher(Room room) : cachedSolutions({}),
                                                roomPlayer(new RoomPlayer(room)),
                                                phase(ObjectiveReacherPhase::NOTHING),
                                                currentRoom(std::nullopt),
                                                currentObjective(std::nullopt),
                                                pathfindingSolution(std::nullopt),
                                                solution(std::nullopt),
                                                pathfindingProblem(std::nullopt),
                                                pathfindingSearcher(std::nullopt),
                                                roomProblem(std::nullopt),
                                                simulationSearcher(std::nullopt){};

ObjectiveReacher::~ObjectiveReacher()
{
    delete this->roomPlayer;
    if (this->pathfindingProblem)
    {
        delete this->pathfindingProblem.value();
    }
    if (this->pathfindingSearcher)
    {
        delete this->pathfindingSearcher.value();
    }
    if (this->roomProblem)
    {
        delete this->roomProblem.value();
    }
    if (this->simulationSearcher)
    {
        delete this->simulationSearcher.value();
    }
};

RoomPlayer *ObjectiveReacher::getRoomPlayer()
{
    return this->roomPlayer;
}

Solution<DerivedRoom, Action> ObjectiveReacher::findSolution(DerivedRoom room, Objective objective)
{
    this->start(room, objective);
    while (this->phase != ObjectiveReacherPhase::FINISHED)
    {
        this->nextPhase();
    }
    this->phase = ObjectiveReacherPhase::NOTHING;
    return this->solution.value();
};

void ObjectiveReacher::start(DerivedRoom room, Objective objective)
{
    if (this->pathfindingProblem)
    {
        delete this->pathfindingProblem.value();
    }
    if (this->pathfindingSearcher)
    {
        delete this->pathfindingSearcher.value();
    }
    if (this->roomProblem)
    {
        delete this->roomProblem.value();
    }
    if (this->simulationSearcher)
    {
        delete this->simulationSearcher.value();
    }
    this->currentRoom = room;
    this->currentObjective = objective;
    this->pathfindingSolution = std::nullopt;
    this->solution = std::nullopt;
    this->pathfindingProblem = std::nullopt;
    this->pathfindingSearcher = std::nullopt;
    this->roomProblem = std::nullopt;
    this->simulationSearcher = std::nullopt;
    this->phase = ObjectiveReacherPhase::CHECK_CACHE;
}

void ObjectiveReacher::nextPhase()
{
    switch (this->phase)
    {
    case ObjectiveReacherPhase::NOTHING:
        break; // Do nothing
    case ObjectiveReacherPhase::CHECK_CACHE:
    {
        Objective objective = this->currentObjective.value();
        auto foundSolutionPtr = this->cachedSolutions.find({this->currentRoom.value(), this->currentObjective.value()});
        if (foundSolutionPtr != this->cachedSolutions.end())
        {
            this->solution = std::get<1>(*foundSolutionPtr);
            this->phase = ObjectiveReacherPhase::FINISHED;
        }
        else if (std::holds_alternative<ReachObjective>(objective) ||
                 std::holds_alternative<StabObjective>(objective))
        {
            this->preparePathfindingPhase();
            this->phase = ObjectiveReacherPhase::PATHFIND;
        }
        else if (OrObjective *orObjective = std::get_if<OrObjective>(&objective))
        {
            bool hasReachOrStab = false;
            for (auto subObjective : orObjective->objectives)
            {
                if (std::holds_alternative<ReachObjective>(subObjective) ||
                    std::holds_alternative<StabObjective>(subObjective))
                {
                    hasReachOrStab = true;
                    break;
                }
            }
            if (hasReachOrStab)
            {
                this->preparePathfindingPhase();
                this->phase = ObjectiveReacherPhase::PATHFIND;
            }
            else
            {
                this->prepareSimulationPhase();
                this->phase = ObjectiveReacherPhase::SIMULATE_ROOM;
            }
        }
        else
        {
            this->prepareSimulationPhase();
            this->phase = ObjectiveReacherPhase::SIMULATE_ROOM;
        }
        break;
    }
    case ObjectiveReacherPhase::PATHFIND:
    {
        this->pathfindingSolution = this->finishPathfindingPhase();
        if (this->pathfindingSolution.value().exists)
        {
            this->prepareSimulationPhase();

            this->phase = ObjectiveReacherPhase::SIMULATE_ROOM;
        }
        else
        {
            this->solution = Solution<DerivedRoom, Action>(false, std::nullopt, std::nullopt, FailureReason::FAILED_PRECHECK);
            this->phase = ObjectiveReacherPhase::FINISHED;
        }
        break;
    }
    case ObjectiveReacherPhase::SIMULATE_ROOM:
    {
        this->solution = this->finishSimulationPhase();
        this->cachedSolutions.insert({{this->currentRoom.value(), this->currentObjective.value()}, this->solution.value()});
        this->phase = ObjectiveReacherPhase::FINISHED;
        break;
    }
    case ObjectiveReacherPhase::FINISHED:
        break; // Do nothing
    default:
        throw std::invalid_argument("Unknown phase");
    }
}

ObjectiveReacherPhase ObjectiveReacher::getPhase()
{
    return this->phase;
}

Solution<DerivedRoom, Action> ObjectiveReacher::getSolution()
{
    return this->solution.value();
}

Searcher<Position, Action> *ObjectiveReacher::getPathfindingSearcher()
{
    return this->pathfindingSearcher.value();
}

Searcher<DerivedRoom, Action> *ObjectiveReacher::getRoomSimulationSearcher()
{
    return this->simulationSearcher.value();
}

// Private methods

void ObjectiveReacher::preparePathfindingPhase()
{
    Position start = std::get<0>(this->currentRoom.value().findPlayer());
    Objective objective = this->currentObjective.value();
    if (OrObjective *obj = std::get_if<OrObjective>(&objective))
    {
        for (auto subObj : obj->objectives)
        {
            if (std::holds_alternative<ReachObjective>(subObj) ||
                std::holds_alternative<StabObjective>(subObj))
            {
                objective = subObj;
                break;
            }
        }
    }
    this->roomPlayer->setActions(this->currentRoom.value().getActions());
    Room pathfindingRoom = this->roomPlayer->getRoom();
    if (ReachObjective *obj = std::get_if<ReachObjective>(&objective))
    {
        this->pathfindingProblem = new PathfindingProblem(start, pathfindingRoom, obj->tiles);
    }
    else if (StabObjective *obj = std::get_if<StabObjective>(&objective))
    {
        std::set<Position> goals = {};
        for (auto tilePtr = obj->tiles.begin(); tilePtr != obj->tiles.end(); ++tilePtr)
        {
            int x = std::get<0>(*tilePtr);
            int y = std::get<1>(*tilePtr);
            goals.insert({{x + 1, y},
                          {x + 1, y + 1},
                          {x, y + 1},
                          {x - 1, y + 1},
                          {x - 1, y},
                          {x - 1, y - 1},
                          {x, y - 1},
                          {x + 1, y - 1}});
        }
        this->pathfindingProblem = new PathfindingProblem(start, pathfindingRoom, goals);
    }
    else
    {
        throw std::invalid_argument("Unknown objective type");
    }
    this->pathfindingSearcher = new Searcher<Position, Action>(this->pathfindingProblem.value());
}

Solution<Position, Action> ObjectiveReacher::finishPathfindingPhase()
{
    return this->pathfindingSearcher.value()->findSolution();
}

void ObjectiveReacher::prepareSimulationPhase()
{
    std::map<Position, int> heuristicTiles = {};
    // If a pathfinding solution exists, prioritize tiles on the found path.
    if (this->pathfindingSolution.has_value())
    {
        std::vector<Action> actions = this->pathfindingSolution.value().actions.value();
        int currentHeuristicValue = actions.size();
        Position currentPosition = std::get<0>(this->currentRoom.value().findPlayer());
        heuristicTiles[currentPosition] = currentHeuristicValue;
        for (auto it = actions.begin(); it != actions.end(); ++it)
        {
            currentPosition = movePosition(currentPosition, *it);
            currentHeuristicValue = currentHeuristicValue - 1;
            heuristicTiles.insert({currentPosition, currentHeuristicValue});
        }
    }
    this->roomProblem = new DerivedRoomProblem(this->roomPlayer,
                                               this->currentRoom.value(),
                                               this->currentObjective.value(),
                                               heuristicTiles);
    // Low iteration limit for now, to avoid finding the solution indirectly by accident
    // Set pathCostInPriority=false, to use greedy best-first search for performance
    this->simulationSearcher = new Searcher<DerivedRoom, Action>(this->roomProblem.value(), true, true, false, 100);
}

Solution<DerivedRoom, Action> ObjectiveReacher::finishSimulationPhase()
{
    return this->simulationSearcher.value()->findSolution();
}