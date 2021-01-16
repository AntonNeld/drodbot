import asyncio
from pydantic import BaseModel, Field
from typing import Tuple, Optional, List

from common import Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .pathfinding import get_position_after
from .room_solver import solve_room, ReachTileObjective
from room import Level, Direction, Element

_ACTION_DELAY = 0.1


class DrodBotState(BaseModel):
    """The state of DRODbot.

    Parameters
    ----------
    level
        The level it's playing.
    current_room
        The current room being played.
    current_position
        The current position in the current room.
    plan
        The current plan to execute.
    """

    level: Level = Field(default_factory=lambda: Level())
    current_room: Tuple[int, int] = (0, 0)
    current_position: Optional[Tuple[int, int]]
    plan: List[Action] = []

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

    Attributes
    ----------
    state
        The current DRODbot state.
    """

    def __init__(self, state_file, drod_interface):
        self._state_file = state_file
        self._interface = drod_interface
        self._state_subscribers = []
        try:
            self.state = DrodBotState.parse_file(self._state_file)
            print(f"Loaded state from {self._state_file}")
        except FileNotFoundError:
            self.state = DrodBotState()

    def subscribe_to_state_update(self, callback):
        """Subscribe to changes in the state.

        Parameters
        ----------
        callback
            A function that will be called when the state is updated.
            Will be called with a DrodBotState instance.
        """
        self._state_subscribers.append(callback)

    def _notify_state_update(self):
        for callback in self._state_subscribers:
            callback(self.state)

    async def initialize(self):
        """Focus the window and get the room content."""
        await self._interface.initialize()
        if self.state.current_room not in self.state.level.rooms:
            await self._interpret_room()

    async def save_state(self):
        """Save the current state to disk."""
        with open(self._state_file, "w") as f:
            f.write(self.state.json())
        print(f"Saved state to {self._state_file}")

    async def go_to(self, element):
        """Go to the nearest tile with the given element.

        Parameters
        ----------
        element
            The element to go to.
        """
        player_position = self.state.current_position
        room = self.state.get_current_room().copy(deep=True)
        # TODO: Use the real direction
        room.tiles[player_position].monster = (Element.BEETHRO, Direction.SE)
        goal_tiles = room.find_coordinates(element)
        actions = solve_room(room, ReachTileObjective(goal_tiles=goal_tiles))
        self.state.plan = actions
        await self._execute_plan()

    async def cross_edge(self):
        """Go to the nearest edge tile and cross into a new room."""
        player_position = self.state.current_position
        room = self.state.get_current_room().copy(deep=True)
        # TODO: Use the real direction
        room.tiles[player_position].monster = (Element.BEETHRO, Direction.SE)
        goal_tiles = (
            [(0, y) for y in range(32)]
            + [(x, 0) for x in range(38)]
            + [(37, y) for y in range(32)]
            + [(x, 31) for x in range(38)]
        )
        actions = solve_room(room, ReachTileObjective(goal_tiles=goal_tiles))
        x, y = get_position_after(actions, player_position)
        if x == 0:
            actions.append(Action.W)
        elif x == ROOM_WIDTH_IN_TILES - 1:
            actions.append(Action.E)
        elif y == 0:
            actions.append(Action.N)
        elif y == ROOM_HEIGHT_IN_TILES - 1:
            actions.append(Action.S)
        self.state.plan = actions
        await self._execute_plan()

    async def reinterpret_room(self):
        """Reinterpret the current room, and replace its state."""
        await self._interpret_room()

    async def _interpret_room(self):
        print("Interpreting room...")
        visual_info = await self._interface.get_view()
        room = visual_info["room"]
        self.state.current_position = room.find_player()
        # Remove Beethro from the room, so the saved level doesn't
        # have a bunch of Beethros standing around
        room.tiles[self.state.current_position].monster = (
            Element.NOTHING,
            Direction.NONE,
        )
        self.state.set_current_room(room)
        self._notify_state_update()
        print("Interpreted room")

    async def _execute_plan(self):
        print("Executing plan...")
        while self.state.plan:
            action = self.state.plan.pop(0)
            x, y = self.state.current_position
            if x == ROOM_WIDTH_IN_TILES - 1 and action == Action.E:
                await self._enter_room(Direction.E)
            elif x == ROOM_WIDTH_IN_TILES - 1 and action in [Action.SE, Action.NE]:
                raise RuntimeError(f"Tried to move {action} out of the room")
            elif x == 0 and action == Action.W:
                await self._enter_room(Direction.W)
            elif x == 0 and action in [Action.SW, Action.NW]:
                raise RuntimeError(f"Tried to move {action} out of the room")
            elif y == ROOM_HEIGHT_IN_TILES - 1 and action == Action.S:
                await self._enter_room(Direction.S)
            elif y == ROOM_HEIGHT_IN_TILES - 1 and action in [Action.SW, Action.SE]:
                raise RuntimeError(f"Tried to move {action} out of the room")
            elif y == 0 and action == Action.N:
                await self._enter_room(Direction.N)
            elif y == 0 and action in [Action.NW, Action.NE]:
                raise RuntimeError(f"Tried to move {action} out of the room")
            else:
                await self._interface.do_action(action)
                self.state.current_position = get_position_after(
                    [action], self.state.current_position
                )
            self._notify_state_update()
            await asyncio.sleep(_ACTION_DELAY)
        print("Executed plan")

    async def _enter_room(self, direction):
        """Enter a new room.

        The player must be on the correct edge for this to work.

        Parameters
        ----------
        direction
            The direction to go in. Cannot be diagonal.
        """
        print(f"Entering new room in direction {direction.value}")
        room_x, room_y = self.state.current_room
        player_x, player_y = self.state.current_position
        if direction == Direction.N:
            if player_y != 0:
                raise RuntimeError(f"Cannot enter new room by moving N, y={player_y}")
            action = Action.N
            new_room_coords = (room_x, room_y - 1)
            position_after = (player_x, ROOM_HEIGHT_IN_TILES - 1)
        elif direction == Direction.W:
            if player_x != 0:
                raise RuntimeError(f"Cannot enter new room by moving W, x={player_x}")
            action = Action.W
            new_room_coords = (room_x - 1, room_y)
            position_after = (ROOM_WIDTH_IN_TILES - 1, player_y)
        elif direction == Direction.S:
            if player_y != ROOM_HEIGHT_IN_TILES - 1:
                raise RuntimeError(f"Cannot enter new room by moving S, y={player_y}")
            action = Action.S
            new_room_coords = (room_x, room_y + 1)
            position_after = (player_x, 0)
        elif direction == Direction.E:
            if player_x != ROOM_WIDTH_IN_TILES - 1:
                raise RuntimeError(f"Cannot enter new room by moving E, x={player_x}")
            action = Action.E
            new_room_coords = (room_x + 1, room_y)
            position_after = (0, player_y)
        else:
            raise RuntimeError(f"Unknown direction {direction}")
        await self._interface.do_action(action)
        # Wait for the animation to finish
        await asyncio.sleep(1)
        self.state.current_room = new_room_coords
        if new_room_coords in self.state.level.rooms:
            self.state.current_position = position_after
            self._notify_state_update()
        else:
            await self._interpret_room()
