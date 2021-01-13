import asyncio
from pydantic import BaseModel, Field
from typing import Tuple

from common import Action
from .pathfinding import find_path
from room import Level, Direction

_ACTION_DELAY = 0.1


class DrodBotState(BaseModel):
    """The state of DRODbot.

    Parameters
    ----------
    level
        The level it's playing.
    current_room
        The current room being played.
    """

    level: Level = Field(default_factory=lambda: Level())
    current_room: Tuple[int, int] = (0, 0)

    def get_current_room(self):
        """Get the current room.

        Returns
        -------
        The current room contents.
        """
        return self.level.rooms[self.current_room]

    def set_current_room(self, room):
        """Set the current room.

        Parameters
        ----------
        room
            The current room contents.
        """
        self.level.rooms[self.current_room] = room


class DrodBot:
    """This class is responsible for playing DROD.

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
        await self._interpret_room()

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
        room = self._state.get_current_room()
        player_position = room.find_player()
        goal_positions = room.find_coordinates(element)
        actions = find_path(player_position, goal_positions, room)
        await self._do_actions(actions)

    async def go_to_edge(self):
        """Go to the nearest edge tile."""
        room = self._state.get_current_room()
        player_position = room.find_player()
        goal_positions = (
            [(0, y) for y in range(32)]
            + [(x, 0) for x in range(38)]
            + [(37, y) for y in range(32)]
            + [(x, 31) for x in range(38)]
        )
        actions = find_path(player_position, goal_positions, room)
        await self._do_actions(actions)

    async def enter_room(self, direction):
        """Enter a new room.

        The player must be on the correct edge for this to work.

        Parameters
        ----------
        direction
            The direction to go in. Cannot be diagonal.
        """
        x, y = self._state.current_room
        if direction == Direction.N:
            action = Action.N
            new_coords = (x, y - 1)
        elif direction == Direction.W:
            action = Action.W
            new_coords = (x - 1, y)
        elif direction == Direction.S:
            action = Action.S
            new_coords = (x, y + 1)
        elif direction == Direction.E:
            action = Action.E
            new_coords = (x + 1, y)
        else:
            raise RuntimeError(f"Unknown direction {direction}")
        await self._interface.do_action(action)
        # Wait for the animation to finish
        await asyncio.sleep(1)
        self._state.current_room = new_coords
        await self._interpret_room()

    async def _interpret_room(self):
        print("Interpreting room...")
        visual_info = await self._interface.get_view()
        self._state.set_current_room(visual_info["room"])
        print("Interpreted room")

    async def _do_actions(self, actions):
        for action in actions:
            await self._interface.do_action(action)
            await asyncio.sleep(_ACTION_DELAY)
