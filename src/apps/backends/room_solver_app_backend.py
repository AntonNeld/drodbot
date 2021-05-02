import time

from common import GUIEvent, UserError, RoomSolverGoal
from room_simulator import (
    Objective,
    ElementType,
    Room,
    RoomProblem,
    PathfindingProblem,
    SearcherRoomAction,
    SearcherPositionAction,
)


class RoomSolverAppBackend:
    """The backend for the room solver app.

    Parameters
    ----------
    play_interface
        The interface for playing rooms, to initialize it.
    room_interpreter
        The room interpreter, to get a room from a screenshot.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(self, play_interface, room_interpreter, bot, window_queue):
        self._queue = window_queue
        self._interface = play_interface
        self._interpreter = room_interpreter
        self._bot = bot
        self._room = None
        self._searcher = None
        # Keep a reference to the problem. Since the C++ code gets
        # a reference to it, we don't want it to be garbage collected.
        self._problem = None

    async def get_room_from_screenshot(self):
        """Set the current room from a screenshot."""
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        self._room = await self._interpreter.get_initial_room()
        print(f"Interpreted room in {time.time()-t:.2f}s")
        self._show_data()

    async def get_room_from_bot(self):
        """Set the current room to the current room from the bot."""
        self._room = self._bot.get_current_room()
        self._show_data()

    async def init_search(self, goal, use_heuristic):
        """Initialize a search for the selected goal.

        Parameters
        ----------
        goal
            The RoomSolverGoal to reach.
        use_heuristic
            Whether to use a heuristic function.
        """
        if self._room is None:
            raise UserError("Must get a room before searching")
        if goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN_PATHFINDING:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            start, _ = self._room.find_player()
            self._problem = PathfindingProblem(
                start, self._room, set(conquer_tokens), use_heuristic=use_heuristic
            )
            self._searcher = SearcherPositionAction(self._problem)
        elif goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN_ROOM_SIMULATION:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            objective = Objective(sword_at_tile=False, tiles=set(conquer_tokens))
            self._problem = RoomProblem(
                self._room, objective, use_heuristic=use_heuristic
            )
            self._searcher = SearcherRoomAction(self._problem)
        self._show_data()

    async def expand_next_node(self):
        """Expand the next node in the room solver."""
        if self._searcher is None:
            raise UserError("Must initialize search before expanding nodes")
        self._searcher.expand_next_node()
        self._show_data()

    async def rewind_expansion(self):
        """Go back to the previous node in the room solver."""
        if self._searcher is None:
            raise UserError("Must initialize search before expanding nodes")
        iterations = self._searcher.get_iterations()
        self._searcher.reset()
        for _ in range(iterations - 1):
            self._searcher.expand_next_node()
        self._show_data()

    async def find_solution(self):
        """Search until we find a solution."""
        if self._searcher is None:
            raise UserError("Must initialize search before searching")
        self._searcher.find_solution()
        self._show_data()

    def _show_data(self):
        if self._searcher is None:
            searcher_data = None
            room = self._room
        else:
            searcher_data = _extract_searcher_info(self._searcher)
            if isinstance(searcher_data["current_state"], Room):
                room = searcher_data["current_state"]
            else:
                room = self._room

        reconstructed_image = self._interpreter.reconstruct_room_image(room)
        self._queue.put(
            (GUIEvent.SET_ROOM_SOLVER_DATA, reconstructed_image, room, searcher_data)
        )


def _extract_searcher_info(searcher):
    return {
        "iterations": searcher.get_iterations(),
        "current_path": searcher.get_current_path(),
        "current_state": searcher.get_current_state(),
        "found_solution": searcher.found_solution(),
        "current_state_heuristic": searcher.get_current_state_heuristic(),
        "frontier_states": searcher.get_frontier_states(),
        "explored_states": searcher.get_explored(),
    }
