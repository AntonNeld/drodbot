#ifndef DRODBOT_DERIVEDROOMPROBLEM_H
#define DRODBOT_DERIVEDROOMPROBLEM_H

#include <map>
#include "../Room.h"
#include "../DerivedRoom.h"
#include "../objectives/Objective.h"
#include "../typedefs.h"
#include "../search/Problem.h"
#include "../RoomPlayer.h"

class DerivedRoomProblem final : public Problem<DerivedRoom, Action>
{
public:
    DerivedRoomProblem(Room room, Objective objective, std::map<Position, int> heuristicTiles = {});
    DerivedRoom initialState();
    std::set<Action> actions(DerivedRoom state);
    DerivedRoom result(DerivedRoom state, Action action);
    bool goalTest(DerivedRoom state);
    int stepCost(DerivedRoom state, Action action, DerivedRoom result);
    int heuristic(DerivedRoom state);

private:
    RoomPlayer roomPlayer;
    Objective objective;
    std::map<Position, int> heuristicTiles;
};

#endif // DRODBOT_DERIVEDROOMPROBLEM_H