from room_simulator import (
    ObjectiveReacher,
    PlanningProblem,
    SearcherDerivedRoomObjective,
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
    objective_reacher = ObjectiveReacher(room)
    problem = PlanningProblem(objective, objective_reacher)
    searcher = SearcherDerivedRoomObjective(problem)
    solution = searcher.find_solution()
    if not solution.exists:
        raise NoSolutionError(
            iteration_limited=solution.failure_reason
            == FailureReason.ITERATION_LIMIT_REACHED
        )
    return expand_planning_solution(solution.actions, objective_reacher)
