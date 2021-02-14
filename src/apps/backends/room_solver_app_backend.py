import time

from common import GUIEvent, UserError, Action
from room import Room


class RoomSolverAppBackend:
    """The backend for the room solver app.

    Parameters
    ----------
    play_interface
        The interface for playing rooms, used to interpret screenshots.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(self, play_interface, window_queue):
        self._queue = window_queue
        self._interface = play_interface
        self._room = None

    async def get_room(self):
        """Set the current room from a screenshot."""
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        tile_contents, orb_effects, debug_images = await self._interface.get_view(
            return_debug_images=True
        )
        self._room = Room.from_apparent_tiles(tile_contents, orb_effects)
        reconstructed_tile_contents = self._room.to_apparent_tiles()
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                next(image for name, image in debug_images if name == "Extract room"),
                reconstructed_tile_contents,
            )
        )
        print(f"Interpreted room in {time.time()-t:.2f}s")

    async def simulate_move_east(self):
        """Simulate moving east in the current room."""
        if self._room is None:
            raise UserError("Must get a room before simulating")
        self._room.do_action(Action.E, in_place=True)
        tile_contents = self._room.to_apparent_tiles()
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                None,
                tile_contents,
            )
        )
