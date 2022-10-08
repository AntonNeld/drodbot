import json
import os
import os.path
from typing import List, Union
import time

from room_simulator import (
    OrObjective,
    ReachObjective,
    MonsterCountObjective,
    StabObjective,
    Room,
)
from drod_bot import solve_room
from search import NoSolutionError
from util import room_from_dict, objective_from_dict


class Test:
    file_name: str
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective]
    room: Room

    def __init__(
        self,
        file_name: str,
        objective: Union[
            OrObjective, ReachObjective, StabObjective, MonsterCountObjective
        ],
        room: Room,
    ):
        self.file_name = file_name
        self.objective = objective
        self.room = room

    @staticmethod
    def from_json(file_name: str, json_string: str):
        content = json.loads(json_string)
        return Test(
            file_name,
            objective_from_dict(content["objective"]),
            room_from_dict(content["room"]),
        )


def test_rooms(test_room_dir: str):
    """Test saved rooms

    Parameters
    ----------
    test_room_dir
        Location of saved rooms
    """
    tests = _load_test_rooms(test_room_dir)
    for test in tests:
        try:
            time_before = time.time()
            solve_room(test.room, test.objective)
            time_taken = time.time() - time_before
            print(f"Solved test room {test.file_name} in {time_taken}s")
        except NoSolutionError:
            print(f"FAILED to solve test room {test.file_name}")


def _load_test_rooms(test_room_dir: str) -> List[Test]:
    test_rooms = []
    for file_name in os.listdir(test_room_dir):
        with open(os.path.join(test_room_dir, file_name), "r") as f:
            test_rooms.append(Test.from_json(file_name, f.read()))

    return test_rooms
