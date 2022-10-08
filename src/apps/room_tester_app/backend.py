from asyncio import AbstractEventLoop
import queue
from typing import Optional, List
from dataclasses import dataclass, field

import numpy
from apps.util import run_coroutine
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
        self._active_test_name: Optional[str] = None

    def get_queue(self):
        """Get a queue with state updates.

        Returns
        -------
        The queue
        """
        return self._queue

    def load_tests(self):
        """Load tests."""
        run_coroutine(self._load_tests(), self._event_loop)

    async def _load_tests(self):
        self._room_tester.load_test_rooms()
        self._push_state_update()

    def set_active_test(self, test_name: str):
        """Set the active test.

        test_name
            The name of the test to set as active
        """
        self._active_test_name = test_name
        self._push_state_update()

    def run_tests(self):
        """Run all tests."""
        run_coroutine(self._run_tests(), self._event_loop)

    async def _run_tests(self):
        self._room_tester.run_tests()
        self._push_state_update()

    def _push_state_update(self):
        if self._active_test_name is not None:
            active_test = next(
                t
                for t in self._room_tester.get_tests()
                if t.file_name == self._active_test_name
            )
            room = active_test.room
            room_image = self._interpreter.reconstruct_room_image(room)
        else:
            room = None
            room_image = None
        self._queue.put(
            RoomTesterAppState(
                active_test_room=room,
                active_test_room_image=room_image,
                tests=self._room_tester.get_tests(),
            )
        )
