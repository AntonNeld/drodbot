import asyncio
import random

from common import Action


class DrodBot:
    def __init__(self, drod_interface, window_queue):
        self._interface = drod_interface
        self._queue = window_queue

    async def move_randomly_forever(self):
        while True:
            await asyncio.sleep(0.1)
            action = random.choice(list(Action))
            await self._interface.do_action(action)

    async def show_view(self):
        image = await self._interface.get_view()
        self._queue.put(("display_image", image))
