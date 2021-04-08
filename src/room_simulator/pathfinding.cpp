#include <array>
#include <vector>
#include <set>
#include "Room.h"
#include "typedefs.h"
#include "search/Problem.h"

class PathfindingProblem : public Problem<Position, Action>
{
public:
    PathfindingProblem(Position startPosition,
                       Room room,
                       std::set<Position> goals) : startPosition(startPosition),
                                                   room(room),
                                                   goals(goals)
    {
    }
    Position initialState()
    {
        return this->startPosition;
    }

    std::vector<Action> actions(Position state)
    {
        std::vector<Action> actions;
        int x = std::get<0>(state);
        int y = std::get<1>(state);
        if (this->room.isPassable(x + 1, y))
        {
            actions.push_back(Action::E);
        }
        if (this->room.isPassable(x + 1, y + 1))
        {
            actions.push_back(Action::SE);
        }
        if (this->room.isPassable(x, y + 1))
        {
            actions.push_back(Action::S);
        }
        if (this->room.isPassable(x - 1, y + 1))
        {
            actions.push_back(Action::SW);
        }
        if (this->room.isPassable(x - 1, y))
        {
            actions.push_back(Action::W);
        }
        if (this->room.isPassable(x - 1, y - 1))
        {
            actions.push_back(Action::NW);
        }
        if (this->room.isPassable(x, y - 1))
        {
            actions.push_back(Action::N);
        }
        if (this->room.isPassable(x + 1, y - 1))
        {
            actions.push_back(Action::NE);
        }
        return actions;
    }

    Position result(Position state, Action action)
    {
        int x = std::get<0>(state);
        int y = std::get<1>(state);
        switch (action)
        {
        case Action::E:
            return {x + 1, y};
        case Action::SE:
            return {x + 1, y + 1};
        case Action::S:
            return {x, y + 1};
        case Action::SW:
            return {x - 1, y + 1};
        case Action::W:
            return {x - 1, y};
        case Action::NW:
            return {x - 1, y - 1};
        case Action::N:
            return {x, y - 1};
        case Action::NE:
            return {x + 1, y - 1};
        default:
            return {x, y};
        }
    }

    bool goalTest(Position state)
    {
        return this->goals.find(state) != goals.end();
    }

    int stepCost(Position state, Action action, Position result)
    {
        return 1;
    }

private:
    Position startPosition;
    Room room;
    std::set<Position> goals;
};

std::vector<Action> findPath(Position start, std::vector<Position> goals, Room room)
{
    std::set<Position> obstacles = {};
    std::array<ElementType, 8> obstacleTypes = {ElementType::WALL,
                                                ElementType::MASTER_WALL,
                                                ElementType::OBSTACLE,
                                                ElementType::YELLOW_DOOR,
                                                ElementType::BLUE_DOOR,
                                                ElementType::GREEN_DOOR,
                                                ElementType::ORB,
                                                ElementType::PIT};
    for (unsigned int i = 0; i < obstacleTypes.size(); i += 1)
    {
        std::vector<Position> coords = room.findCoordinates(obstacleTypes[i]);
        for (unsigned int j = 0; j < coords.size(); j += 1)
        {
            obstacles.insert(coords[j]);
        }
    }
    // TODO: Implement pre-check?
    // TODO: Implement search
    return {Action::E};
}
