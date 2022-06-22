from enum import Enum

from apps.util import GUIEvent
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
        The DRODbot itself.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(self, bot, window_queue):
        self._bot = bot
        self._bot.subscribe_to_state_update(self._push_state_update)
        self._queue = window_queue
        self._queue.put((GUIEvent.SET_PLAYING_DATA, self._bot.state))

    async def run_strategy(self, strategy):
        """Have Beethro do something, usually trying to solve the room.

        Parameters
        ----------
        strategy
            The strategy to execute.
        """
        await self._bot.initialize()
        if strategy == Strategy.MOVE_TO_CONQUER_TOKEN:
            await self._bot.go_to_element_in_room(ElementType.CONQUER_TOKEN)
        elif strategy == Strategy.MOVE_TO_CONQUER_TOKEN_IN_LEVEL:
            await self._bot.go_to_element_in_level(ElementType.CONQUER_TOKEN)
        elif strategy == Strategy.GO_TO_UNVISITED_ROOM:
            await self._bot.go_to_unvisited_room()
        elif strategy == Strategy.GO_TO_EAST_ROOM:
            await self._bot.go_to_room_in_direction(Direction.E)
        elif strategy == Strategy.GO_TO_SOUTH_ROOM:
            await self._bot.go_to_room_in_direction(Direction.S)
        elif strategy == Strategy.GO_TO_WEST_ROOM:
            await self._bot.go_to_room_in_direction(Direction.W)
        elif strategy == Strategy.GO_TO_NORTH_ROOM:
            await self._bot.go_to_room_in_direction(Direction.N)
        elif strategy == Strategy.EXPLORE:
            await self._bot.explore_level_continuously()
        elif strategy == Strategy.EXPLORE_AND_CONQUER:
            await self._bot.explore_level_continuously(conquer_rooms=True)
        elif strategy == Strategy.STRIKE_ORB:
            await self._bot.strike_element(ElementType.ORB)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    async def save_state(self):
        """Save the DRODbot state to disk."""
        await self._bot.save_state()

    async def clear_state(self):
        """Clear the DRODbot state."""
        await self._bot.clear_state()

    async def recheck_room(self):
        """Interpret the current room again and replace the state."""
        await self._bot.reinterpret_room()

    def _push_state_update(self, state):
        self._queue.put((GUIEvent.SET_PLAYING_DATA, state))
