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


class RoomTester:
    """Tests saved rooms.

    Parameters
    ----------
    test_room_dir
        Location of saved test rooms
    """

    def __init__(self, test_room_dir: str):
        self._test_room_dir = test_room_dir
        self._tests: List[Test] = []
        self._failed_tests: List[Test] = []

    def load_test_rooms(self):
        self._tests = []
        for file_name in os.listdir(self._test_room_dir):
            with open(os.path.join(self._test_room_dir, file_name), "r") as f:
                self._tests.append(Test.from_json(file_name, f.read()))

    def run_tests(self):
        self._failed_tests = []
        for test in self._tests:
            try:
                time_before = time.time()
                solve_room(test.room, test.objective)
                time_taken = time.time() - time_before
                print(f"Solved test room {test.file_name} in {time_taken}s")
            except NoSolutionError:
                print(f"Failed to solve test room {test.file_name}")
                self._failed_tests.append(test)

    def get_tests(self):
        return self._tests

    def get_failed_tests(self):
        return self._failed_tests
