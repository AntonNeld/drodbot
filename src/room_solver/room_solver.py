from room_simulator import (
    AStarSearcherPositionAction,
    AStarSearcherRoomAction,
    PathfindingProblem,
    RoomProblem,
)


class RoomSolver:
    def __init__(self, room, objective):
        self.room = room
        self.objective = objective

    def find_solution(self, simple_pathfinding=False):
        if simple_pathfinding:
            start, _ = self.room.find_player()
            problem = PathfindingProblem(start, self.room, self.objective.tiles)
            searcher = AStarSearcherPositionAction(problem)
        else:
            problem = RoomProblem(self.room, self.objective)
            searcher = AStarSearcherRoomAction(problem)
        return searcher.find_solution()

    def get_iterations(self):
        return 0
