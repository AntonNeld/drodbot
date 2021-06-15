from room_simulator import (
    ObjectiveReacher,
    PlanningProblem,
    SearcherRoomObjective,
    FailureReason,
)
from search import NoSolutionError


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
    sub_objectives = solution.actions
    actions = []
    latest_room = room
    for sub_objective in sub_objectives:
        sub_solution = objective_reacher.find_solution(latest_room, sub_objective)
        actions.extend(sub_solution.actions)
        latest_room = sub_solution.final_state
    return actions
