from common import Strategy


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
        self._queue = window_queue

    async def run_strategy(self, strategy):
        """Have Beethro do something, usually trying to solve the room.

        Parameters
        ----------
        strategy
            The strategy to execute.
        """
        if strategy == Strategy.MOVE_RANDOMLY:
            await self._bot.run_strategy(strategy)
        elif strategy == Strategy.MOVE_TO_CONQUER_TOKEN:
            await self._bot.run_strategy(strategy)
        else:
            raise RuntimeError(f"Unknown strategy {strategy}")
