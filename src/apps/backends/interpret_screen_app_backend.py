from common import GUIEvent
from room import room_from_apparent_tiles


class InterpretScreenAppBackend:
    """The backend for the interpret screen app.

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

    async def show_view(self):
        """Show the given view step in the GUI.

        This method will add the image and tile contents to the window queue.
        """
        await self._interface.initialize()
        tile_contents, orb_effects, debug_images = await self._interface.get_view(
            return_debug_images=True
        )
        room = room_from_apparent_tiles(tile_contents, orb_effects)
        self._queue.put((GUIEvent.SET_INTERPRET_SCREEN_DATA, debug_images, room))
