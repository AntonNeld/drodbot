from asyncio import AbstractEventLoop
from enum import Enum
import queue

from apps.util import run_coroutine
from drod_bot.drod_bot import DrodBot, SaveTestRoomBehavior
from drod_bot.state.drod_bot_state import DrodBotState
from room_simulator import ElementType, Direction


# The values are also what will be displayed in the GUI
class Strategy(str, Enum):
    """A strategy for what Beethro should do."""

    EXPLORE_AND_CONQUER = "Explore while conquering rooms"
    EXPLORE = "Explore the current level"
    GO_TO_UNVISITED_ROOM = "Go to the nearest unvisited room"
    GO_TO_EAST_ROOM = "Go to the room east of here"
    GO_TO_SOUTH_ROOM = "Go to the room south of here"
    GO_TO_WEST_ROOM = "Go to the room west of here"
    GO_TO_NORTH_ROOM = "Go to the room north of here"
    MOVE_TO_CONQUER_TOKEN = "Move to a conquer token in the room"
    MOVE_TO_CONQUER_TOKEN_IN_LEVEL = "Move to a conquer token anywhere in the level"
    STRIKE_ORB = "Strike the nearest orb"


class PlayingAppBackend:
    """The backend for the playing app.

    Parameters
    ----------
    bot
        The DRODbot itself
    event_loop
        The asyncio event loop
    """

    def __init__(self, bot: DrodBot, event_loop: AbstractEventLoop):
        self._bot = bot
        self._bot.subscribe_to_state_update(self._push_state_update)
        self._queue: queue.Queue[DrodBotState] = queue.Queue()
        self._queue.put(self._bot.state)
        self._event_loop = event_loop

    def get_queue(self):
        """Get a queue with state updates.

        Returns
        -------
        The queue
        """
        return self._queue

    def run_strategy(
        self,
        strategy: Strategy,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        """Have Beethro do something, usually trying to solve the room.

        Parameters
        ----------
        strategy
            The strategy to execute.
        save_test_rooms
            Whether and which rooms to save for regression tests.
        """
        run_coroutine(
            self._async_run_strategy(strategy, save_test_rooms=save_test_rooms),
            self._event_loop,
        )

    async def _async_run_strategy(
        self,
        strategy: Strategy,
        save_test_rooms: SaveTestRoomBehavior = SaveTestRoomBehavior.NO_SAVING,
    ):
        await self._bot.initialize()
        if strategy == Strategy.MOVE_TO_CONQUER_TOKEN:
            await self._bot.go_to_element_in_room(
                ElementType.CONQUER_TOKEN, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.MOVE_TO_CONQUER_TOKEN_IN_LEVEL:
            await self._bot.go_to_element_in_level(
                ElementType.CONQUER_TOKEN, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.GO_TO_UNVISITED_ROOM:
            await self._bot.go_to_unvisited_room(save_test_rooms=save_test_rooms)
        elif strategy == Strategy.GO_TO_EAST_ROOM:
            await self._bot.go_to_room_in_direction(
                Direction.E, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.GO_TO_SOUTH_ROOM:
            await self._bot.go_to_room_in_direction(
                Direction.S, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.GO_TO_WEST_ROOM:
            await self._bot.go_to_room_in_direction(
                Direction.W, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.GO_TO_NORTH_ROOM:
            await self._bot.go_to_room_in_direction(
                Direction.N, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.EXPLORE:
            await self._bot.explore_level_continuously(save_test_rooms=save_test_rooms)
        elif strategy == Strategy.EXPLORE_AND_CONQUER:
            await self._bot.explore_level_continuously(
                conquer_rooms=save_test_rooms, save_test_rooms=save_test_rooms
            )
        elif strategy == Strategy.STRIKE_ORB:
            await self._bot.strike_element(
                ElementType.ORB, save_test_rooms=save_test_rooms
            )
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    def save_state(self):
        """Save the DRODbot state to disk."""
        run_coroutine(self._bot.save_state(), self._event_loop)

    def clear_state(self):
        """Clear the DRODbot state."""
        run_coroutine(self._bot.clear_state(), self._event_loop)

    def recheck_room(self):
        """Interpret the current room again and replace the state."""
        run_coroutine(self._bot.reinterpret_room(), self._event_loop)

    def _push_state_update(self, state: DrodBotState):
        self._queue.put(state)
