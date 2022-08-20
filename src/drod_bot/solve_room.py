from enum import Enum
from pathlib import Path
from typing import Optional

from room_simulator import (
    ObjectiveReacher,
    PlanningProblem,
    Room,
    SearcherDerivedRoomObjective,
    FailureReason,
)
from search import NoSolutionError
from util import expand_planning_solution


class SaveTestRoomBehavior(str, Enum):
    """Whether and which rooms+objectives to save for regression tests."""

    NO_SAVING = "Don't save rooms"
    SAVE_ALL = "Save all room+objective combinations"


def solve_room(
    room: Room,
    objective,
    save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    test_room_location: Optional[Path | str] = None,
):
    """Find a sequence of actions to solve a room.

    Parameters
    ----------
    room
        The room to solve
    objective
        The objective to reach.
    save_test_rooms
        Whether and which rooms to save for regression tests.
    test_room_location
        Where to save test rooms. Can only be None if
        save_test_rooms is NO_SAVING.
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
    maybe_save_room(room, save_test_rooms, test_room_location)
    return expand_planning_solution(solution.actions, objective_reacher)


def maybe_save_room(
    room: Room,
    save_test_rooms: SaveTestRoomBehavior,
    test_room_location: Optional[Path | str] = None,
):
    """Possibly save the room, depending on save_test_rooms.

    Parameters
    ----------
    room
        The room
    save_test_rooms
        Behavior around saving test rooms
    test_room_location
        Where to save test rooms
    """
    if save_test_rooms != SaveTestRoomBehavior.NO_SAVING and test_room_location is None:
        raise RuntimeError("test_room_location needs to be set if saving test rooms")
    if save_test_rooms != SaveTestRoomBehavior.NO_SAVING:
        print(f"TODO: Save room to {test_room_location}")
