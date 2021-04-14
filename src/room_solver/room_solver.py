from room_simulator import (
    AStarSearcherPositionAction,
    AStarSearcherRoomAction,
    PathfindingProblem,
    RoomProblem,
)


class RoomSolver:
    """Solves a room.

    Parameters
    ----------
    room
        The room to solve.
    objective
        The objective to reach in the room.
    simple_pathfinding
        Whether to use simple pathfinding instead of trying to solve the room
        with a more general algorithm.
    """

    def __init__(self, room, objective, simple_pathfinding=False):
        if simple_pathfinding:
            start, _ = room.find_player()
            problem = PathfindingProblem(start, room, objective.tiles)
            self.searcher = AStarSearcherPositionAction(problem)
        else:
            problem = RoomProblem(room, objective)
            self.searcher = AStarSearcherRoomAction(problem)

    def find_solution(self):
        """Find the solution.

        This is the only method needed for serious use, the others are only
        for inspecting the algorithm.

        Returns
        -------
        A list of actions.
        """
        return self.searcher.find_solution()

    def get_iterations(self):
        """Get the number of iterations we've gone through.

        Returns
        -------
        The number of iterations.
        """
        return 0
