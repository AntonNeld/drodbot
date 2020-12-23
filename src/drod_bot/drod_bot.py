import asyncio
import random

from common import Action, GUIEvent


class DrodBot:
    def __init__(self, drod_interface, window_queue):
        self._interface = drod_interface
        self._queue = window_queue

    async def move_randomly_forever(self):
        visual_info = await self._interface.get_view()
        await self._interface.focus_window(visual_info)
        while True:
            await asyncio.sleep(0.1)
            action = random.choice(list(Action))
            await self._interface.do_action(action)

    async def show_view(self, step):
        visual_info = await self._interface.get_view(step)
        self._queue.put((GUIEvent.DISPLAY_IMAGE, visual_info["image"]))
