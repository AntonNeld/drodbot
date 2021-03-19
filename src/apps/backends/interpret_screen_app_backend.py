import time

from common import GUIEvent


class InterpretScreenAppBackend:
    """The backend for the interpret screen app.

    Parameters
    ----------
    play_interface
        The play interface, so we can initialize it before showing the view.
    room_interpreter
        The room interpreter.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(self, play_interface, room_interpreter, window_queue):
        self._interface = play_interface
        self._interpreter = room_interpreter
        self._queue = window_queue

    async def show_view(self):
        """Show the given view step in the GUI.

        This method will add the image and tile contents to the window queue.
        """
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        room, debug_images = await self._interpreter.get_initial_room(
            return_debug_images=True
        )
        print(f"Interpreted room in {time.time()-t:.2f}s")
        self._queue.put((GUIEvent.SET_INTERPRET_SCREEN_DATA, debug_images, room))
