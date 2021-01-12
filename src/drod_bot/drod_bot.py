import asyncio

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
        self._room = None

    async def initialize(self):
        """Focus the window and get the room content."""
        await self._interface.initialize()
        print("Interpreting room...")
        visual_info = await self._interface.get_view()
        self._room = visual_info["room"]
        print("Interpreted room")

    async def go_to(self, element):
        """Go to the nearest tile with the given element.

        Parameters
        ----------
        element
            The element to go to.
        """
        player_position = self._room.find_player()
        goal_positions = self._room.find_coordinates(element)
        actions = find_path(player_position, goal_positions, self._room)
        await self._do_actions(actions)

    async def go_to_edge(self):
        """Go to the nearest edge tile."""
        player_position = self._room.find_player()
        goal_positions = (
            [(0, y) for y in range(32)]
            + [(x, 0) for x in range(38)]
            + [(37, y) for y in range(32)]
            + [(x, 31) for x in range(38)]
        )
        actions = find_path(player_position, goal_positions, self._room)
        await self._do_actions(actions)

    async def _do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(_ACTION_DELAY)
