import asyncio
import random

from common import Action, Strategy, Element
from .pathfinding import find_path

ACTION_DELAY = 0.1


class DrodBot:
    def __init__(self, drod_interface, window_queue):
        self._interface = drod_interface
        self._queue = window_queue

    async def run_strategy(self, strategy):
        await self._interface.initialize()
        visual_info = await self._interface.get_view()
        room = visual_info["room"]
        if strategy == Strategy.MOVE_RANDOMLY:
            actions = random.choices(list(Action), k=30)
            await self.do_actions(actions)
        elif strategy == Strategy.MOVE_TO_CONQUER_TOKEN:
            player_position = room.find_player()
            conquer_positions = room.find_coordinates(Element.CONQUER_TOKEN)
            actions = find_path(player_position, conquer_positions, room)
            await self.do_actions(actions)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    async def do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(ACTION_DELAY)
