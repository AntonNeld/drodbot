#include "../Room.h"
#include "../Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"

class RoomProblem : public Problem<Room, Action>
{
public:
    RoomProblem(Room room, Objective objective);
    Room initialState();
    std::set<Action> actions(Room state);
    Room result(Room state, Action action);
    bool goalTest(Room state);
    int stepCost(Room state, Action action, Room result);
    int heuristic(Room state);

private:
    Room room;
    Objective objective;
};