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

    async def show_view_step(self, step):
        """Show the given view step in the GUI.

        This method will add the image and room to the window queue.

        Parameters
        ----------
        step
            The step to stop at.
        """
        visual_info = await self._interface.get_view(step)
        self._queue.put(
            (
                GUIEvent.SET_INTERPRET_SCREEN_DATA,
                visual_info["image"],
                visual_info["room"] if "room" in visual_info else None,
            )
        )
