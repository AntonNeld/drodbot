import time

from common import GUIEvent


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

    async def get_room(self):
        """Set the current room from a screenshot."""
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        tile_contents, _, debug_images = await self._interface.get_view(
            return_debug_images=True
        )
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                next(image for name, image in debug_images if name == "Extract room"),
                tile_contents,
            )
        )
        print(f"Interpreted room in {time.time()-t:.2f}s")
