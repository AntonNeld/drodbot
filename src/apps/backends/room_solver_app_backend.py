import time

import numpy

from common import (
    GUIEvent,
    ROOM_HEIGHT_IN_TILES,
    ROOM_WIDTH_IN_TILES,
    TILE_SIZE,
    UserError,
)
from room_simulator import Action, simulate_action


class RoomSolverAppBackend:
    """The backend for the room solver app.

    Parameters
    ----------
    play_interface
        The interface for playing rooms, to initialize it.
    room_interpreter
        The room interpreter, to get a room from a screenshot.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(self, play_interface, room_interpreter, bot, window_queue):
        self._queue = window_queue
        self._interface = play_interface
        self._interpreter = room_interpreter
        self._bot = bot
        self._room = None

    async def get_room_from_screenshot(self):
        """Set the current room from a screenshot."""
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        room, debug_images = await self._interpreter.get_initial_room(
            return_debug_images=True
        )
        self._room = room
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                next(image for name, image in debug_images if name == "Extract room"),
                self._room,
            )
        )
        print(f"Interpreted room in {time.time()-t:.2f}s")

    async def get_room_from_bot(self):
        """Set the current room to the current room from the bot."""
        self._room = self._bot.get_current_room()
        # Let's create an empty image for now
        room_image = (
            numpy.ones(
                (ROOM_HEIGHT_IN_TILES * TILE_SIZE, ROOM_WIDTH_IN_TILES * TILE_SIZE, 3),
                dtype=numpy.uint8,
            )
            * 127
        )
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                room_image,
                self._room,
            )
        )

    async def simulate_move_east(self):
        """Simulate moving east in the current room."""
        if self._room is None:
            raise UserError("Must get a room before simulating")
        self._room = simulate_action(self._room, Action.E)
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                None,
                self._room,
            )
        )
