import asyncio
from pathlib import Path
import time
from typing import Callable, List

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from drod_interface.play_interface import PlayInterface
from room_interpreter.room_interpreter import RoomInterpreter
from util import position_in_direction
from .solve_room import solve_room, SaveTestRoomBehavior
from .level_walker import find_path_in_level
from room_interpreter import RoomText, get_room_text
from room_simulator import (
    ElementType,
    Direction,
    Element,
    Action,
    simulate_actions,
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
    test_room_location
        Where to save test rooms.
    drod_interface
        The interface for playing rooms.

    Attributes
    ----------
    state
        The current DRODbot state.
    """

    def __init__(
        self,
        state_file: str | Path,
        test_room_location: str | Path,
        drod_interface: PlayInterface,
        room_interpreter: RoomInterpreter,
    ):
        self._state_file = state_file
        self._test_room_location = test_room_location
        self._interface = drod_interface
        self._interpreter = room_interpreter
        self._state_subscribers: List[Callable[[DrodBotState], None]] = []
        try:
            self.state = DrodBotState.parse_file(self._state_file)
            print(f"Loaded state from {self._state_file}")
        except FileNotFoundError:
            self.state = DrodBotState()

    def subscribe_to_state_update(self, callback: Callable[[DrodBotState], None]):
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

    async def clear_state(self):
        """Clear the current state."""
        self.state = DrodBotState()
        print("Cleared state")
        self._notify_state_update()

    async def go_to_element_in_room(
        self,
        element: ElementType,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Go to the nearest tile with the given element.

        We will not leave the current room.

        Parameters
        ----------
        element
            The element to go to.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        print("Thinking...")
        t = time.time()
        room = self.state.current_room
        goal_tiles = room.find_coordinates(element)
        actions = solve_room(
            room,
            ReachObjective(tiles=set(goal_tiles)),
            save_test_rooms=save_test_rooms,
            test_room_location=self._test_room_location,
        )
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()

    async def go_to_element_in_level(
        self,
        element: ElementType,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Go to the nearest tile with the given element.

        This works across rooms, as long as the element and path
        to it are in known rooms.

        Parameters
        ----------
        element
            The element to go to.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        goal_tiles = self.state.level.find_element(element)
        print("Thinking...")
        t = time.time()
        actions = find_path_in_level(
            goal_tiles,
            self.state.current_room,
            self.state.current_room_position,
            self.state.level,
            save_test_rooms=save_test_rooms,
            test_room_location=self._test_room_location,
        )
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()

    async def go_to_unvisited_room(
        self, save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING
    ):
        """Enter the nearest unvisited room.

        Parameters
        ----------
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        goal_tiles = self.state.level.find_uncrossed_edges()
        print("Trying to go to an unvisited room...")
        t = time.time()
        try:
            actions = find_path_in_level(
                goal_tiles,
                self.state.current_room,
                self.state.current_room_position,
                self.state.level,
                save_test_rooms=save_test_rooms,
                test_room_location=self._test_room_location,
            )
            print(f"Thought in {time.time()-t:.2f}s, found a solution")
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
        except NoSolutionError as e:
            print(f"Thought in {time.time()-t:.2f}s, did not find a solution")
            raise e

    async def go_to_room_in_direction(
        self,
        direction: Direction,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Go to the room in the given direction.

        Orthogonal directions only.

        Parameters
        ----------
        direction
            The direction.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        print("Thinking...")
        t = time.time()
        exits = self.state.level.get_room_exits(
            self.state.current_room_position, allow_unexplored_target=True
        )
        if direction == Direction.N:
            goal_tiles = [e[0] for e in exits if e[0][1] == 0]
            last_action = Action.N
        elif direction == Direction.E:
            goal_tiles = [e[0] for e in exits if e[0][0] == ROOM_WIDTH_IN_TILES - 1]
            last_action = Action.E
        elif direction == Direction.S:
            goal_tiles = [e[0] for e in exits if e[0][1] == ROOM_HEIGHT_IN_TILES - 1]
            last_action = Action.S
        elif direction == Direction.W:
            goal_tiles = [e[0] for e in exits if e[0][0] == 0]
            last_action = Action.W
        actions = solve_room(
            self.state.current_room,
            ReachObjective(tiles=set(goal_tiles)),
            save_test_rooms=save_test_rooms,
            test_room_location=self._test_room_location,
        )
        actions.append(last_action)
        print(f"Thought in {time.time()-t:.2f}s")
        self.state.plan = actions
        await self._execute_plan()

    async def explore_level_continuously(
        self,
        conquer_rooms=False,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Explore the level while there are unvisited rooms.

        Parameters
        ----------
        conquer_rooms
            Whether to conquer the current room if possible.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        while True:
            if conquer_rooms and not self.state.current_room.is_conquered():
                try:
                    await self.conquer_room(save_test_rooms=save_test_rooms)
                    continue
                except NoSolutionError:
                    print(
                        "Can't conquer current room from here, checking other entrances"
                    )
            if conquer_rooms and not self.state.current_room.is_conquered():
                exits = self.state.level.get_room_exits(
                    self.state.current_room_position,
                    allow_unexplored_target=True,
                )
                possible_entrances = []
                for exit in exits:
                    position, _, _ = exit
                    if position == self.state.current_room.find_player()[0]:
                        # We already tried this one
                        continue
                    print(f"Trying {position}...")
                    t = time.time()
                    room = self.state.level.rooms[
                        self.state.current_room_position
                    ].copy()
                    tile = room.get_tile(position)
                    tile.monster = Element(
                        # Make up a direction
                        element_type=ElementType.BEETHRO,
                        direction=Direction.SW,
                    )
                    room.set_tile(position, tile)
                    try:
                        solve_room(
                            room,
                            MonsterCountObjective(monsters=0),
                            save_test_rooms=save_test_rooms,
                            test_room_location=self._test_room_location,
                        )
                        print(f"Thought in {time.time()-t:.2f}s, found a solution")
                        possible_entrances.append(position)
                    except NoSolutionError:
                        print(
                            f"Thought in {time.time()-t:.2f}s, "
                            "did not find a solution"
                        )
                self.state.room_backlog.extend(
                    [
                        (self.state.current_room_position, pos)
                        for pos in possible_entrances
                    ]
                )
            if self.state.room_backlog:
                try:
                    print("Trying to reach a room entrance from the backlog...")
                    t = time.time()
                    actions = find_path_in_level(
                        self.state.room_backlog,
                        self.state.current_room,
                        self.state.current_room_position,
                        self.state.level,
                        save_test_rooms=save_test_rooms,
                        test_room_location=self._test_room_location,
                    )
                    print(f"Thought in {time.time()-t:.2f}s, found a solution")
                    self.state.plan = actions
                    await self._execute_plan()
                    continue
                except NoSolutionError:
                    print(f"Thought in {time.time()-t:.2f}s, did not find a solution")
            try:
                await self.go_to_unvisited_room(save_test_rooms=save_test_rooms)
                continue
            except NoSolutionError:
                pass
            if self.state.just_conquered_current_room:
                try:
                    print("Just conquered current room, trying to leave it...")
                    t = time.time()
                    exits = self.state.level.get_room_exits(
                        self.state.current_room_position
                    )
                    actions = find_path_in_level(
                        [e[2] for e in exits],
                        self.state.current_room,
                        self.state.current_room_position,
                        self.state.level,
                        save_test_rooms=save_test_rooms,
                        test_room_location=self._test_room_location,
                    )
                    print(f"Thought in {time.time()-t:.2f}s, found a solution")
                    self.state.plan = actions
                    await self._execute_plan()
                    continue
                except NoSolutionError:
                    print(f"Thought in {time.time()-t:.2f}s, did not find a solution")
            try:
                print("Trying to reach stairs...")
                t = time.time()
                stair_tiles = self.state.level.find_element(ElementType.STAIRS)
                actions = find_path_in_level(
                    stair_tiles,
                    self.state.current_room,
                    self.state.current_room_position,
                    self.state.level,
                    save_test_rooms=save_test_rooms,
                    test_room_location=self._test_room_location,
                )
                self.state.plan = actions
                print(f"Thought in {time.time()-t:.2f}s")
                await self._execute_plan()
                continue
            except NoSolutionError:
                print(f"Thought in {time.time()-t:.2f}s, " "did not find a solution")
            print("Done exploring")
            break

    async def strike_element(
        self,
        element: ElementType,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Strike the nearest instance of the given element with the sword.

        Parameters
        ----------
        element
            The element to strike.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        room = self.state.current_room
        goal_tiles = room.find_coordinates(element)
        actions = solve_room(
            room,
            StabObjective(tiles=set(goal_tiles)),
            save_test_rooms=save_test_rooms,
            test_room_location=self._test_room_location,
        )
        self.state.plan = actions
        await self._execute_plan()

    async def conquer_room(
        self, save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING
    ):
        """Conquer the current room.

        Parameters
        ----------
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        print("Trying to conquer current room...")
        t = time.time()
        try:
            room = self.state.current_room
            actions = solve_room(
                room,
                MonsterCountObjective(monsters=0),
                save_test_rooms=save_test_rooms,
                test_room_location=self._test_room_location,
            )
            print(f"Thought in {time.time()-t:.2f}s, found a solution")
            self.state.plan = actions
            await self._execute_plan()
            # Remove the conquered room from the backlog
            self.state.room_backlog = [
                r
                for r in self.state.room_backlog
                if r[0] != self.state.current_room_position
            ]
            # Remove monsters from the room in the level
            self.state.level.rooms[self.state.current_room_position].make_conquered()
            self.state.just_conquered_current_room = True
        except NoSolutionError as e:
            print(f"Thought in {time.time()-t:.2f}s, did not find a solution")
            raise e

    async def reinterpret_room(self):
        """Reinterpret the current room, and replace its state."""
        await self._interface.initialize()
        await self._interpret_room()

    async def _interpret_room(self):
        print("Interpreting room...")
        t = time.time()
        room, room_text = await self._interpreter.get_initial_room()
        if room_text in [RoomText.EXIT_LEVEL, RoomText.EXIT_LEVEL_AND_SECRET_ROOM]:
            self.state.level.clear()
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
            elif (
                self.state.current_room.get_tile(
                    position_in_direction((x, y), action)
                ).room_piece.element_type
                == ElementType.STAIRS
            ):
                await self._interface.do_action(action)
                await self._leave_level()
            else:
                await self._interface.do_action(action)
                self.state.current_room = simulate_actions(
                    self.state.current_room, [action]
                )
            self._notify_state_update()
            await asyncio.sleep(_ACTION_DELAY)

    async def _enter_room(self, direction: Direction):
        """Enter a new room.

        The player must be on the correct edge for this to work.

        Parameters
        ----------
        direction
            The direction to go in. Cannot be diagonal.
        """
        if self.state.current_room is None:
            raise RuntimeError("No current room")
        print(f"Entering new room in direction {direction.name}")
        room_x, room_y = self.state.current_room_position
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
        self.state.just_conquered_current_room = False
        if new_room_coords in self.state.level.rooms:
            room_image, _ = await self._interface.get_room_image()
            room_text = get_room_text(room_image)
            if room_text in [RoomText.EXIT_LEVEL, RoomText.EXIT_LEVEL_AND_SECRET_ROOM]:
                self.state.level.clear()
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

    async def _leave_level(self):
        print("Leaving level")
        # Let's watch Beethro walk down the stairs for a while
        await asyncio.sleep(3)
        await self._interface.do_action(Action.WAIT)
        # Let's read the entrance text for a while
        await asyncio.sleep(3)
        await self._interface.do_action(Action.WAIT)
        # Let's wait a little while for the swirly animation to stop
        await asyncio.sleep(3)

        self.state = DrodBotState()
        await self._interpret_room()
