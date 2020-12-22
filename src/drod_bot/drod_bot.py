import asyncio
import random

from common import Action


class DrodBot:
    def __init__(self, drod_interface):
        self._interface = drod_interface

    async def move_randomly_forever(self):
        while True:
            await asyncio.sleep(0.1)
            action = random.choice(list(Action))
            await self._interface.do_action(action)
