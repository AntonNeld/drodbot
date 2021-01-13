import asyncio
from pydantic import BaseModel
from typing import Optional

from .pathfinding import find_path
from room import Level

_ACTION_DELAY = 0.1


class DrodBotState(BaseModel):
    level: Optional[Level]


class DrodBot:
    """This class if responsible for playing DROD.

    Parameters
    ----------
    state_file
        File to save and load DRODbot state, like knowledge about
        visited rooms.
    drod_interface
        The interface for playing rooms.
    """

    def __init__(self, state_file, drod_interface):
        self._state_file = state_file
        self._interface = drod_interface
        try:
            self._state = DrodBotState.parse_file(self._state_file)
            print(f"Loaded state from {self._state_file}")
        except FileNotFoundError:
            self._state = DrodBotState()

    async def initialize(self):
        """Focus the window and get the room content."""
        await self._interface.initialize()
        print("Interpreting room...")
        visual_info = await self._interface.get_view()
        self._state.level = Level()
        self._state.level.rooms[(0, 0)] = visual_info["room"]
        print("Interpreted room")

    async def save_state(self):
        """Save the current state to disk."""
        with open(self._state_file, "w") as f:
            f.write(self._state.json())
        print(f"Saved state to {self._state_file}")

    async def go_to(self, element):
        """Go to the nearest tile with the given element.

        Parameters
        ----------
        element
            The element to go to.
        """
        player_position = self._state.level.rooms[(0, 0)].find_player()
        goal_positions = self._state.level.rooms[(0, 0)].find_coordinates(element)
        actions = find_path(
            player_position, goal_positions, self._state.level.rooms[(0, 0)]
        )
        await self._do_actions(actions)

    async def go_to_edge(self):
        """Go to the nearest edge tile."""
        player_position = self._state.level.rooms[(0, 0)].find_player()
        goal_positions = (
            [(0, y) for y in range(32)]
            + [(x, 0) for x in range(38)]
            + [(37, y) for y in range(32)]
            + [(x, 31) for x in range(38)]
        )
        actions = find_path(
            player_position, goal_positions, self._state.level.rooms[(0, 0)]
        )
        await self._do_actions(actions)

    async def _do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(_ACTION_DELAY)
