from enum import Enum
from pathlib import Path
from typing import Optional, Union
import json
import os
import os.path

from room_simulator import (
    ObjectiveReacher,
    OrObjective,
    ReachObjective,
    MonsterCountObjective,
    StabObjective,
    PlanningProblem,
    Room,
    SearcherDerivedRoomObjective,
    FailureReason,
)
from search import NoSolutionError
from util import expand_planning_solution, objective_to_dict, room_to_dict


class SaveTestRoomBehavior(str, Enum):
    """Whether and which rooms+objectives to save for regression tests."""

    NO_SAVING = "Don't save rooms"
    SAVE_ALL = "Save all room+objective combinations"


def solve_room(
    room: Room,
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective],
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
    _maybe_save_room(room, objective, save_test_rooms, test_room_location)
    return expand_planning_solution(solution.actions, objective_reacher)


def _maybe_save_room(
    room: Room,
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective],
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
    if save_test_rooms == SaveTestRoomBehavior.NO_SAVING:
        pass
    elif save_test_rooms == SaveTestRoomBehavior.SAVE_ALL:
        _save_test_room(room, objective, test_room_location)
    else:
        raise RuntimeError(f"Unknown SaveTestRoomBehavior {save_test_rooms}")


def _save_test_room(
    room: Room,
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective],
    test_room_location: Optional[Path | str],
):
    if test_room_location is None:
        raise RuntimeError("test_room_location needs to be set if saving test rooms")
    if not os.path.exists(test_room_location):
        os.makedirs(test_room_location)
    file_content = json.dumps(
        {"objective": objective_to_dict(objective), "room": room_to_dict(room)}
    )
    file_name = hex(abs(hash(file_content))).replace("0x", "")
    print(f"Saving room+objective as {file_name}")
    with open(os.path.join(test_room_location, f"{file_name}.json"), "w") as f:
        f.write(file_content)
