import time

from common import GUIEvent, UserError, RoomSolverGoal
from room_simulator import Objective, ElementType
from room_solver import RoomSolver


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
        self._room_solver = None

    async def get_room_from_screenshot(self):
        """Set the current room from a screenshot."""
        print("Interpreting room...")
        t = time.time()
        await self._interface.initialize()
        self._room = await self._interpreter.get_initial_room()
        print(f"Interpreted room in {time.time()-t:.2f}s")
        self._show_data(self._room)

    async def get_room_from_bot(self):
        """Set the current room to the current room from the bot."""
        self._room = self._bot.get_current_room()
        self._show_data(self._room)

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
        if goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            objective = Objective(sword_at_tile=False, tiles=set(conquer_tokens))
        self._room_solver = RoomSolver(
            self._room, objective, simple_pathfinding=True, use_heuristic=use_heuristic
        )
        self._show_data(
            self._room, room_solver_data=_extract_solver_info(self._room_solver)
        )

    async def expand_next_node(self):
        """Expand the next node in the room solver."""
        if self._room_solver is None:
            raise UserError("Must initialize search before expanding nodes")
        self._room_solver.expand_next_node()
        self._show_data(
            self._room, room_solver_data=_extract_solver_info(self._room_solver)
        )

    async def rewind_expansion(self):
        """Go back to the previous node in the room solver."""
        if self._room_solver is None:
            raise UserError("Must initialize search before expanding nodes")
        self._room_solver.rewind_expansion()
        self._show_data(
            self._room, room_solver_data=_extract_solver_info(self._room_solver)
        )

    async def find_solution(self):
        """Search until we find a solution."""
        if self._room_solver is None:
            raise UserError("Must initialize search before searching")
        self._room_solver.find_solution()
        self._show_data(
            self._room, room_solver_data=_extract_solver_info(self._room_solver)
        )

    def _show_data(self, room, room_solver_data=None):
        reconstructed_image = self._interpreter.reconstruct_room_image(room)
        self._queue.put(
            (GUIEvent.SET_ROOM_SOLVER_DATA, reconstructed_image, room, room_solver_data)
        )


def _extract_solver_info(room_solver):
    return {
        "iterations": room_solver.get_iterations(),
        "current_path": room_solver.get_current_path(),
        "current_state": room_solver.get_current_state(),
        "found_solution": room_solver.found_solution(),
        "current_state_heuristic": room_solver.get_current_state_heuristic(),
        "frontier_states": room_solver.get_frontier_states(),
        "explored_states": room_solver.get_explored(),
    }
