import time

from common import (
    GUIEvent,
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
        self._room = await self._interpreter.get_initial_room()
        print(f"Interpreted room in {time.time()-t:.2f}s")
        self._show_room(self._room)

    async def get_room_from_bot(self):
        """Set the current room to the current room from the bot."""
        self._room = self._bot.get_current_room()
        self._show_room(self._room)

    async def simulate_move_east(self):
        """Simulate moving east in the current room."""
        if self._room is None:
            raise UserError("Must get a room before simulating")
        self._room = simulate_action(self._room, Action.E)
        self._show_room(self._room)

    def _show_room(self, room):
        reconstructed_image = self._interpreter.reconstruct_room_image(room)
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                reconstructed_image,
                self._room,
            )
        )
