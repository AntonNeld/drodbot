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
            # Assign the problem to self.problem. Since the C++ code gets
            # a reference to it, we don't want it to be garbage collected.
            self.problem = PathfindingProblem(start, room, objective.tiles)
            self.searcher = AStarSearcherPositionAction(self.problem)
        else:
            # Assign the problem to self.problem. Since the C++ code gets
            # a reference to it, we don't want it to be garbage collected.
            self.problem = RoomProblem(room, objective)
            self.searcher = AStarSearcherRoomAction(self.problem)

    def find_solution(self):
        """Find the solution.

        This is the only method needed for serious use, the others are only
        for inspecting the algorithm.

        Returns
        -------
        A list of actions.
        """
        return self.searcher.find_solution()

    def expand_next_node(self):
        """Expand the next node in the searcher."""
        self.searcher.expand_next_node()

    def get_iterations(self):
        """Get the number of iterations we've gone through.

        Returns
        -------
        The number of iterations.
        """
        return self.searcher.get_iterations()

    def get_current_path(self):
        """Get the path to the current node.

        Returns
        -------
        The actions to reach the current node.
        """
        return self.searcher.get_current_path()

    def get_current_state(self):
        """Get the state of the current node.

        Returns
        -------
        The state of the current node. Either a Room or (x, y) coordinates,
        depending on if simple_pathfinding is True.
        """
        return self.searcher.get_current_state()
