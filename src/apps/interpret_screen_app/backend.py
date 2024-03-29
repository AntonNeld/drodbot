import asyncio
import time
import queue

from room_simulator import Action


class InterpretScreenAppBackend:
    """The backend for the interpret screen app.

    Parameters
    ----------
    play_interface
        The play interface, so we can initialize it before showing the view.
    room_interpreter
        The room interpreter.
    """

    def __init__(self, play_interface, room_interpreter):
        self._interface = play_interface
        self._interpreter = room_interpreter
        self._queue = queue.Queue()

    def get_queue(self):
        """Get a queue with state updates.

        Returns
        -------
        The queue
        """
        return self._queue

    async def get_view(self):
        """Get a view of the room.

        This method will add the debug images and tile contents to the window queue.
        """
        await self._interface.initialize()
        await self._interpret_room()

    async def move_then_get_view(self):
        """Move east, then get a view of the room."""
        await self._interface.initialize()
        await self._interface.do_action(Action.E)
        # Wait for the animation to finish
        await asyncio.sleep(1)
        await self._interpret_room()

    async def _interpret_room(self):
        print("Interpreting room...")
        t = time.time()
        room, room_text, debug_images = await self._interpreter.get_initial_room(
            return_debug_images=True
        )
        reconstructed_image = self._interpreter.reconstruct_room_image(room)
        debug_images.append(("Reconstruct image", reconstructed_image))
        print(f"Interpreted room in {time.time()-t:.2f}s")
        self._queue.put((debug_images, room, room_text))
