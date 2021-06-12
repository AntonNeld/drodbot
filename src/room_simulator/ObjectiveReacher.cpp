#include <vector>
#include <map>
#include <tuple>
#include <optional>
#include "ObjectiveReacher.h"
#include "Objective.h"
#include "typedefs.h"
#include "search/Searcher.h"
#include "problems/RoomProblem.h"

ObjectiveReacher::ObjectiveReacher() : cachedSolutions({}),
                                       phase(ObjectiveReacherPhase::NOTHING),
                                       currentRoom(std::nullopt),
                                       currentObjective(std::nullopt),
                                       solution(std::nullopt),
                                       roomProblem(std::nullopt),
                                       simulationSearcher(std::nullopt){};

ObjectiveReacher::~ObjectiveReacher()
{
    if (this->roomProblem)
    {
        delete this->roomProblem.value();
    }
    if (this->simulationSearcher)
    {
        delete this->simulationSearcher.value();
    }
};

Solution<Room, Action> ObjectiveReacher::findSolution(Room room, Objective objective)
{
    this->start(room, objective);
    while (this->phase != ObjectiveReacherPhase::FINISHED)
    {
        this->nextPhase();
    }
    this->phase = ObjectiveReacherPhase::NOTHING;
    return this->solution.value();
};

void ObjectiveReacher::start(Room room, Objective objective)
{
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
    this->solution = std::nullopt;
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
        auto foundSolutionPtr = this->cachedSolutions.find({this->currentRoom.value(), this->currentObjective.value()});
        if (foundSolutionPtr != this->cachedSolutions.end())
        {
            this->solution = std::get<1>(*foundSolutionPtr);
            this->phase = ObjectiveReacherPhase::FINISHED;
        }
        else
        {
            this->roomProblem = new RoomProblem(this->currentRoom.value(), this->currentObjective.value());
            // Low iteration limit for now, to avoid finding the solution indirectly by accident
            this->simulationSearcher = new Searcher<Room, Action>(this->roomProblem.value(), true, true, false, 100);
            this->phase = ObjectiveReacherPhase::SIMULATE_ROOM;
        }
        break;
    }
    case ObjectiveReacherPhase::SIMULATE_ROOM:
    {
        this->solution = this->simulationSearcher.value()->findSolution();
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

Solution<Room, Action> ObjectiveReacher::getSolution()
{
    return this->solution.value();
}

Searcher<Room, Action> *ObjectiveReacher::getRoomSimulationSearcher()
{
    return this->simulationSearcher.value();
}