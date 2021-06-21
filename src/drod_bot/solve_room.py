from room_simulator import (
    ObjectiveReacher,
    PlanningProblem,
    SearcherRoomObjective,
    FailureReason,
)
from search import NoSolutionError
from util import expand_planning_solution


def solve_room(room, objective):
    """Find a sequence of actions to solve a room.

    Parameters
    ----------
    room
        The room to solve
    objective
        The objective to reach.
    """
    objective_reacher = ObjectiveReacher()
    problem = PlanningProblem(room, objective, objective_reacher)
    searcher = SearcherRoomObjective(problem)
    solution = searcher.find_solution()
    if not solution.exists:
        raise NoSolutionError(
            iteration_limited=solution.failure_reason
            == FailureReason.ITERATION_LIMIT_REACHED
        )
    return expand_planning_solution(room, solution.actions, objective_reacher)
