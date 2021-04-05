#include <array>
#include <vector>
#include <set>
#include "Room.h"
#include "typedefs.h"

std::vector<Action> findPath(Position start, Direction startDirection,
                             std::vector<Position> goals, Room room,
                             bool swordAtGoal = false)
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
    // TODO: Implement pre-check
    // TODO: Implement search
    return {Action::E};
}
