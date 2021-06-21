import asyncio
import time

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .solve_room import solve_room
from .level_walker import find_path_in_level
from room_simulator import (
    ElementType,
    Direction,
    Element,
    Action,
    simulate_action,
    ReachObjective,
    StabObjective,
    MonsterCountObjective,
)
from .state import DrodBotState
from search import NoSolutionError

_ACTION_DELAY = 0.1


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

    def __init__(self, state_file, drod_interface, room_interpreter):
        self._state_file = state_file
        self._interface = drod_interface
        self._interpreter = room_interpreter
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

    def get_current_room(self):
        """Get the current room.

        Returns
        -------
        The current room
        """
        return self.state.current_room

    def _notify_state_update(self):
        for callback in self._state_subscribers:
            callback(self.state)

    async def initialize(self):
        """Focus the window and get the room content."""
        await self._interface.initialize()
        if self.state.current_room_position not in self.state.level.rooms:
            await self._interpret_room()

    async def save_state(self):
        """Save the current state to disk."""
        with open(self._state_file, "w") as f:
            f.write(self.state.json())
        print(f"Saved state to {self._state_file}")

    async def go_to_element_in_room(self, element):
        """Go to the nearest tile with the given element.

        We will not leave the current room.

        Parameters
        ----------
        element
            The element to go to.
        """
        print("Thinking...")
        t = time.time()
        room = self.state.current_room
        goal_tiles = room.find_coordinates(element)
        actions = solve_room(room, ReachObjective(tiles=set(goal_tiles)))
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()

    async def go_to_element_in_level(self, element):
        """Go to the nearest tile with the given element.

        This works across rooms, as long as the element and path
        to it are in known rooms.

        Parameters
        ----------
        element
            The element to go to.
        """
        goal_tiles = self.state.level.find_element(element)
        print("Thinking...")
        t = time.time()
        actions = find_path_in_level(
            goal_tiles,
            self.state.current_room,
            self.state.current_room_position,
            self.state.level,
        )
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()

    async def go_to_unvisited_room(self):
        """Enter the nearest unvisited room."""
        goal_tiles = self.state.level.find_uncrossed_edges()
        print("Thinking...")
        t = time.time()
        actions = find_path_in_level(
            goal_tiles,
            self.state.current_room,
            self.state.current_room_position,
            self.state.level,
        )
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()
        # Actually cross into the room
        (x, y), _ = self.state.current_room.find_player()
        if x == 0:
            self.state.plan = [Action.W]
        elif x == ROOM_WIDTH_IN_TILES - 1:
            self.state.plan = [Action.E]
        elif y == 0:
            self.state.plan = [Action.N]
        elif y == ROOM_HEIGHT_IN_TILES - 1:
            self.state.plan = [Action.S]
        await self._execute_plan()

    async def explore_level_continuously(self, conquer_rooms=False):
        """Explore the level while there are unvisited rooms.

        Parameters
        ----------
        conquer_rooms
            Whether to conquer the current room if possible.
        """
        try:
            while True:
                if conquer_rooms and not self.state.current_room.is_conquered():
                    try:
                        await self.conquer_room()
                    except NoSolutionError:
                        print(
                            "Can't conquer current room from here, "
                            "checking other directions"
                        )
                        exits = self.state.level.get_room_exits(
                            self.state.current_room_position,
                            allow_unexplored_target=True,
                        )
                        possible_entrances = []
                        for exit in exits:
                            position, _, _ = exit
                            room = self.state.level.rooms[
                                self.state.current_room_position
                            ].copy()
                            if position == self.state.current_room.find_player()[0]:
                                # We already tried this one
                                continue
                            tile = room.get_tile(position)
                            tile.monster = Element(
                                # Make up a direction
                                element_type=ElementType.BEETHRO,
                                direction=Direction.SW,
                            )
                            room.set_tile(position, tile)
                            try:
                                solve_room(room, MonsterCountObjective(monsters=0))
                                print(f"Found a solution from {position}")
                                possible_entrances.append(position)
                            except NoSolutionError:
                                pass  # Continue the loop
                        self.state.room_backlog.extend(
                            [
                                (self.state.current_room_position, pos)
                                for pos in possible_entrances
                            ]
                        )
                if self.state.room_backlog:
                    try:
                        actions = find_path_in_level(
                            self.state.room_backlog,
                            self.state.current_room,
                            self.state.current_room_position,
                            self.state.level,
                        )
                        self.state.plan = actions
                        await self._execute_plan()
                    except NoSolutionError:
                        await self.go_to_unvisited_room()
                else:
                    await self.go_to_unvisited_room()
        except NoSolutionError:
            print("Done exploring")

    async def strike_element(self, element):
        """Strike the nearest instance of the given element with the sword.

        Parameters
        ----------
        element
            The element to strike.
        """
        room = self.state.current_room
        goal_tiles = room.find_coordinates(element)
        actions = solve_room(room, StabObjective(tiles=set(goal_tiles)))
        self.state.plan = actions
        await self._execute_plan()

    async def conquer_room(self):
        """Conquer the current room."""
        print("Thinking...")
        t = time.time()
        room = self.state.current_room
        actions = solve_room(room, MonsterCountObjective(monsters=0))
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()
        # Remove the conquered room from the backlog
        self.state.room_backlog = [
            r
            for r in self.state.room_backlog
            if r[0] != self.state.current_room_position
        ]

    async def reinterpret_room(self):
        """Reinterpret the current room, and replace its state."""
        await self._interface.initialize()
        await self._interpret_room()

    async def _interpret_room(self):
        print("Interpreting room...")
        t = time.time()
        room = await self._interpreter.get_initial_room()
        self.state.current_room = room
        room_in_level = room.copy()
        player_position, _ = room_in_level.find_player()
        # Remove Beethro from the room, so the saved level doesn't
        # have a bunch of Beethros standing around
        tile = room_in_level.get_tile(player_position)
        tile.monster = Element()
        room_in_level.set_tile(player_position, tile)
        self.state.level.rooms[self.state.current_room_position] = room_in_level
        self._notify_state_update()
        print(f"Interpreted room in {time.time()-t:.2f}s")

    async def _execute_plan(self):
        while self.state.plan:
            action = self.state.plan.pop(0)
            (x, y), _ = self.state.current_room.find_player()
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
                self.state.current_room = simulate_action(
                    self.state.current_room, action
                )
            self._notify_state_update()
            await asyncio.sleep(_ACTION_DELAY)

    async def _enter_room(self, direction):
        """Enter a new room.

        The player must be on the correct edge for this to work.

        Parameters
        ----------
        direction
            The direction to go in. Cannot be diagonal.
        """
        print(f"Entering new room in direction {direction.name}")
        room_x, room_y = self.state.current_room_position
        if (
            self.state.current_room.is_conquered()
            and not self.state.level.rooms[(room_x, room_y)].is_conquered()
        ):
            # We just conquered the room we're leaving, update it in the level
            self.state.level.rooms[(room_x, room_y)].make_conquered()
        (player_x, player_y), player_direction = self.state.current_room.find_player()
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
        self.state.current_room_position = new_room_coords
        if new_room_coords in self.state.level.rooms:
            room = self.state.level.rooms[new_room_coords].copy()
            tile = room.get_tile(position_after)
            tile.monster = Element(
                element_type=ElementType.BEETHRO, direction=player_direction
            )
            room.set_tile(position_after, tile)
            self.state.current_room = room
            self._notify_state_update()
        else:
            await self._interpret_room()
