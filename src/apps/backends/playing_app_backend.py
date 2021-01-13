from common import Strategy, GUIEvent
from room import Element, Direction


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
            await self._bot.go_to(Element.CONQUER_TOKEN)
        elif strategy == Strategy.GO_TO_EDGE:
            await self._bot.go_to_edge()
        elif strategy == Strategy.ENTER_ROOM_EAST:
            await self._bot.enter_room(Direction.E)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")

    async def save_state(self):
        """Save the DRODbot state to disk."""
        await self._bot.save_state()

    def _push_state_update(self, state):
        self._queue.put((GUIEvent.SET_PLAYING_DATA, state))
