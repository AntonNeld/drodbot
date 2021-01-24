from common import GUIEvent


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

        Parameters
        ----------
        step
            The step to stop at.
        """
        await self._interface.initialize()
        tile_contents, _, debug_images = await self._interface.get_view(
            return_debug_images=True
        )
        self._queue.put(
            (GUIEvent.SET_INTERPRET_SCREEN_DATA, debug_images, tile_contents)
        )
