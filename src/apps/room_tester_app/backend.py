from asyncio import AbstractEventLoop
import queue
from typing import Optional, List
from dataclasses import dataclass, field

import numpy
from room_interpreter import RoomInterpreter

from room_simulator import Room
from room_tester import RoomTester, Test


@dataclass
class RoomTesterAppState:
    active_test_room: Optional[Room] = None
    active_test_room_image: Optional[numpy.ndarray] = None
    tests: List[Test] = field(default_factory=list)


class RoomTesterAppBackend:
    """The backend for the room tester app.

    Parameters
    ----------
    event_loop
        The asyncio event loop
    """

    def __init__(
        self,
        room_tester: RoomTester,
        interpreter: RoomInterpreter,
        event_loop: AbstractEventLoop,
    ):
        self._room_tester = room_tester
        self._interpreter = interpreter
        self._queue: queue.Queue[RoomTesterAppState] = queue.Queue()
        self._queue.put(RoomTesterAppState())
        self._event_loop = event_loop

    def get_queue(self):
        """Get a queue with state updates.

        Returns
        -------
        The queue
        """
        return self._queue

    def load_tests(self):
        """Load tests."""
        self._room_tester.load_test_rooms()
        self._push_state_update(RoomTesterAppState(tests=self._room_tester.get_tests()))

    def set_active_test(self, test_name: str):
        """Set the active test.

        test_name
            The name of the test to set as active
        """
        test = next(
            t for t in self._room_tester.get_tests() if t.file_name == test_name
        )
        room = test.room
        room_image = self._interpreter.reconstruct_room_image(room)
        self._push_state_update(
            RoomTesterAppState(
                active_test_room=room,
                active_test_room_image=room_image,
                tests=self._room_tester.get_tests(),
            )
        )

    def _push_state_update(self, state: RoomTesterAppState):
        self._queue.put(state)
