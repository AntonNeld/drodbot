import json
import os
import os.path
from typing import List, Union, Optional
import time
from dataclasses import dataclass

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


@dataclass
class Test:
    file_name: str
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective]
    room: Room
    passed: Optional[bool] = None
    time_taken: Optional[float] = None

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
        self._marked_test_name: Optional[str] = None

    def load_test_rooms(self):
        self._tests = []
        for file_name in os.listdir(self._test_room_dir):
            with open(os.path.join(self._test_room_dir, file_name), "r") as f:
                self._tests.append(Test.from_json(file_name, f.read()))

    def run_tests(self):
        for test in self._tests:
            try:
                time_before = time.time()
                solve_room(test.room, test.objective)
                time_taken = time.time() - time_before
                test.passed = True
                test.time_taken = time_taken
                print(f"Solved test room {test.file_name} in {time_taken}s")
            except NoSolutionError:
                print(f"Failed to solve test room {test.file_name}")
                test.passed = False

    def get_tests(self):
        return self._tests

    def mark_test(self, name: str):
        self._marked_test_name = name

    def get_marked_test(self):
        if self._marked_test_name is None:
            return None
        return next(
            t for t in self.get_tests() if t.file_name == self._marked_test_name
        )
