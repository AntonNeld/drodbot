import asyncio
import random

from common import Action, GUIEvent, Strategy, Entity
from .pathfinding import find_path

ACTION_DELAY = 0.1


class DrodBot:
    def __init__(self, drod_interface, window_queue):
        self._interface = drod_interface
        self._queue = window_queue

    async def run_strategy(self, strategy):
        visual_info = await self._interface.get_view()
        await self._interface.focus_window(visual_info)
        if strategy == Strategy.MOVE_RANDOMLY:
            actions = random.choices(list(Action), k=30)
            await self.do_actions(actions)
        if strategy == Strategy.MOVE_TO_VICTORY_TOKEN:
            player_position = next(
                pos
                for pos, entities in visual_info["entities"].items()
                if Entity.BEETHRO in entities
            )
            victory_positions = [
                pos
                for pos, entities in visual_info["entities"].items()
                if Entity.VICTORY_TOKEN in entities
            ]
            actions = find_path(
                player_position, victory_positions, visual_info["entities"]
            )
            await self.do_actions(actions)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    async def show_view(self, step):
        visual_info = await self._interface.get_view(step)
        self._queue.put((GUIEvent.DISPLAY_IMAGE, visual_info["image"]))

    async def do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(ACTION_DELAY)
