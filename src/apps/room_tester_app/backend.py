import queue
from typing import Optional, List
from dataclasses import dataclass, field

import numpy

from room_simulator import Room


@dataclass
class RoomTesterAppState:
    active_test_room: Optional[Room] = None
    active_test_room_image: Optional[numpy.ndarray] = None
    tests: List[str] = field(default_factory=list)


class RoomTesterAppBackend:
    """The backend for the room tester app.

    Parameters
    ----------
    event_loop
        The asyncio event loop
    """

    def __init__(self, event_loop):
        self._queue: queue.Queue[RoomTesterAppState] = queue.Queue()
        self._queue.put(RoomTesterAppState(tests=["hej", "hoj"]))
        self._event_loop = event_loop

    def get_queue(self):
        """Get a queue with state updates.

        Returns
        -------
        The queue
        """
        return self._queue

    def set_active_test(self, test: str):
        """Set the active test.

        test
            The name of the test to set as active
        """
        pass
