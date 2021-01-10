import asyncio
import random

from common import Action, Strategy, Element
from .pathfinding import find_path

_ACTION_DELAY = 0.1


class DrodBot:
    """This class if responsible for playing DROD.

    Parameters
    ----------
    drod_interface
        The interface for playing rooms.
    """

    def __init__(self, drod_interface):
        self._interface = drod_interface

    async def run_strategy(self, strategy):
        """Have Beethro do something, usually trying to solve the room.

        Parameters
        ----------
        strategy
            The strategy to execute.
        """
        await self._interface.initialize()
        visual_info = await self._interface.get_view()
        room = visual_info["room"]
        if strategy == Strategy.MOVE_RANDOMLY:
            actions = random.choices(list(Action), k=30)
            await self._do_actions(actions)
        elif strategy == Strategy.MOVE_TO_CONQUER_TOKEN:
            player_position = room.find_player()
            conquer_positions = room.find_coordinates(Element.CONQUER_TOKEN)
            actions = find_path(player_position, conquer_positions, room)
            await self._do_actions(actions)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    async def _do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(_ACTION_DELAY)
