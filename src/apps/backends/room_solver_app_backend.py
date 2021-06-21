import time

from common import GUIEvent, UserError, RoomSolverGoal
from room_simulator import (
    ReachObjective,
    StabObjective,
    MonsterCountObjective,
    OrObjective,
    ElementType,
    Room,
    DerivedRoom,
    PathfindingProblem,
    PlanningProblem,
    SearcherPositionAction,
    SearcherRoomObjective,
    ObjectiveReacher,
    ObjectiveReacherPhase,
    simulate_action,
)
from util import expand_planning_solution


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
        self._searcher = None  # May also be an ObjectiveReacher
        # Keep a reference to the problem. Since the C++ code gets
        # a reference to it, we don't want it to be garbage collected.
        self._problem = None
        # Same here. Note that this is for the objective reacher passed to the
        # planning problem.
        self._objective_reacher_ref = None
        # Inspect solution mode inspects the current solution instead of searching.
        # Due to the global RoomPlayer, this does not work with ObjectiveReacher
        self._inspect_solution_mode = False
        self._inspected_actions_index = 0

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

    async def init_search(
        self,
        goal,
        heuristic_in_priority,
        path_cost_in_priority,
        avoid_duplicates,
        target,
    ):
        """Initialize a search for the selected goal.

        Parameters
        ----------
        goal
            The RoomSolverGoal to reach.
        heuristic_in_priority
            Whether to use a heuristic function when prioritizing nodes to expand.
        path_cost_in_priority
            Whether to use the path cost when prioritizing nodes to expand.
        avoid_duplicates
            Whether to keep track of and avoid duplicates.
        target
            Which square to reach/strike, if applicable.
        """
        if self._room is None:
            raise UserError("Must get a room before searching")
        if goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN_PATHFINDING:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            start, _ = self._room.find_player()
            self._problem = PathfindingProblem(start, self._room, set(conquer_tokens))
            self._searcher = SearcherPositionAction(
                self._problem,
                avoid_duplicates=avoid_duplicates,
                heuristic_in_priority=heuristic_in_priority,
                path_cost_in_priority=path_cost_in_priority,
            )
        elif goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN_PLANNING:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            objective = ReachObjective(tiles=set(conquer_tokens))
            self._objective_reacher_ref = ObjectiveReacher()
            self._problem = PlanningProblem(
                self._room, objective, self._objective_reacher_ref
            )
            self._searcher = SearcherRoomObjective(
                self._problem,
                avoid_duplicates=avoid_duplicates,
                heuristic_in_priority=heuristic_in_priority,
                path_cost_in_priority=path_cost_in_priority,
            )
        elif goal == RoomSolverGoal.MOVE_TO_CONQUER_TOKEN_OBJECTIVE_REACHER:
            conquer_tokens = self._room.find_coordinates(ElementType.CONQUER_TOKEN)
            objective = ReachObjective(tiles=set(conquer_tokens))
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)
        elif goal == RoomSolverGoal.STRIKE_ORB_OBJECTIVE_REACHER:
            orbs = self._room.find_coordinates(ElementType.ORB)
            objective = StabObjective(tiles=set(orbs))
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)
        elif goal == RoomSolverGoal.DECREASE_MONSTERS_OBJECTIVE_REACHER:
            monsters = self._room.monster_count()
            objective = MonsterCountObjective(monsters=monsters - 1)
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)
        elif goal == RoomSolverGoal.MOVE_TO_TARGET_PLANNING:
            objective = ReachObjective(tiles=set([target]))
            self._objective_reacher_ref = ObjectiveReacher()
            self._problem = PlanningProblem(
                self._room, objective, self._objective_reacher_ref
            )
            self._searcher = SearcherRoomObjective(
                self._problem,
                avoid_duplicates=avoid_duplicates,
                heuristic_in_priority=heuristic_in_priority,
                path_cost_in_priority=path_cost_in_priority,
            )
        elif goal == RoomSolverGoal.MOVE_TO_TARGET_OBJECTIVE_REACHER:
            objective = ReachObjective(tiles=set([target]))
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)
        elif goal == RoomSolverGoal.STRIKE_TARGET_OBJECTIVE_REACHER:
            objective = StabObjective(tiles=set([target]))
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)
        elif goal == RoomSolverGoal.KILL_EVERYTHING_PLANNING:
            objective = MonsterCountObjective(monsters=0)
            self._objective_reacher_ref = ObjectiveReacher()
            self._problem = PlanningProblem(
                self._room, objective, self._objective_reacher_ref
            )
            self._searcher = SearcherRoomObjective(
                self._problem,
                avoid_duplicates=avoid_duplicates,
                heuristic_in_priority=heuristic_in_priority,
                path_cost_in_priority=path_cost_in_priority,
            )
        elif goal == RoomSolverGoal.MOVE_TO_MONSTER_OR_KILL_SOMETHING:
            monsters = self._room.find_monster_coordinates()
            objective = OrObjective(
                [
                    ReachObjective(set(monsters)),
                    MonsterCountObjective(self._room.monster_count() - 1),
                ]
            )
            self._searcher = ObjectiveReacher()
            self._searcher.start(self._room, objective)

        self._show_data()

    async def expand_next_node(self):
        """Expand the next node in the searcher.

        If inspecting the objective reacher, this method is executed on its
        internal searcher.
        """
        if self._inspect_solution_mode:
            self._inspected_actions_index += 1
        else:
            searcher = self._get_current_searcher()
            searcher.expand_next_node()
        self._show_data()

    async def rewind_expansion(self):
        """Go back to the previous node in the searcher.

        If inspecting the objective reacher, this method is executed on its
        internal searcher.
        """
        if self._inspect_solution_mode:
            self._inspected_actions_index -= 1
        else:
            searcher = self._get_current_searcher()
            iterations = searcher.get_iterations()
            searcher.reset()
            for _ in range(iterations - 1):
                searcher.expand_next_node()
        self._show_data()

    async def find_solution(self):
        """Search until we find a solution.

        If inspecting the objective reacher, this method is executed on its
        internal searcher.
        """
        if self._inspect_solution_mode:
            self._inspected_actions_index = -1
        else:
            searcher = self._get_current_searcher()
            print("Thinking...")
            t = time.time()
            searcher.find_solution()
            print(f"Thought in {time.time()-t:.2f}s")
        self._show_data()

    async def next_objective_reacher_phase(self):
        """Go to the next phase in the objective reacher."""
        if self._inspect_solution_mode:
            raise UserError("No phases in inspect solution mode")
        if not isinstance(self._searcher, ObjectiveReacher):
            raise UserError("Searcher is not an objective reacher")
        self._searcher.next_phase()
        self._show_data()

    async def set_inspect_solution_mode(self, mode):
        """Turn on or off inspect solution mode.

        Parameters
        ----------
        mode
            Whether it should be on or off.
        """
        self._inspect_solution_mode = mode
        self._inspected_actions_index = 0
        self._show_data()

    def _show_data(self):
        try:
            searcher = self._get_current_searcher()
            if self._inspect_solution_mode:
                searcher_data = _make_solution_inspect_info(
                    searcher,
                    self._inspected_actions_index,
                    self._room,
                    self._objective_reacher_ref,
                )
            else:
                searcher_data = _extract_searcher_info(searcher)
            if isinstance(searcher_data["current_state"], Room):
                room = searcher_data["current_state"]
            elif isinstance(searcher_data["current_state"], DerivedRoom):
                room = searcher_data["current_state"].get_full_room()
            else:
                room = self._room
        except UserError:  # No searcher to show data for
            searcher_data = None
            room = self._room

        if (
            isinstance(self._searcher, ObjectiveReacher)
            and not self._inspect_solution_mode
        ):
            objective_reacher_data = _extract_objective_reacher_info(self._searcher)
            if "solution" in objective_reacher_data:
                solution = objective_reacher_data["solution"]
                if solution.exists:
                    room = solution.final_state
        else:
            objective_reacher_data = None

        reconstructed_image = self._interpreter.reconstruct_room_image(room)
        start_position, _ = self._room.find_player()
        self._queue.put(
            (
                GUIEvent.SET_ROOM_SOLVER_DATA,
                reconstructed_image,
                room,
                start_position,
                searcher_data,
                objective_reacher_data,
            )
        )

    def _get_current_searcher(self):
        if self._searcher is None:
            raise UserError("No searcher initialized")
        if isinstance(self._searcher, ObjectiveReacher):
            phase = self._searcher.get_phase()
            if phase == ObjectiveReacherPhase.SIMULATE_ROOM:
                return self._searcher.get_room_simulation_searcher()
            elif phase == ObjectiveReacherPhase.PATHFIND:
                return self._searcher.get_pathfinding_searcher()
            else:
                raise UserError(
                    f"Current phase {self._searcher.get_phase().name} has no searcher"
                )
        else:
            return self._searcher


def _extract_searcher_info(searcher):
    info = {
        "iterations": searcher.get_iterations(),
        "current_path": searcher.get_current_path(),
        "current_state": searcher.get_current_state(),
        "found_solution": searcher.found_solution(),
        "current_state_heuristic": searcher.get_current_state_heuristic(),
        "frontier_size": searcher.get_frontier_size(),
        "frontier_actions": searcher.get_frontier_actions(),
        "explored_size": searcher.get_explored_size(),
    }
    if isinstance(searcher.get_current_state(), tuple):
        info["frontier_states"] = searcher.get_frontier_states()
        info["explored_states"] = searcher.get_explored()
    return info


def _extract_objective_reacher_info(objective_reacher):
    phase = objective_reacher.get_phase()
    info = {"phase": phase.name}
    if phase == ObjectiveReacherPhase.FINISHED:
        info["solution"] = objective_reacher.get_solution()
    return info


def _make_solution_inspect_info(
    searcher, inspected_actions_index, room, objective_reacher
):
    full_solution = searcher.get_current_path()
    if isinstance(searcher, SearcherRoomObjective):
        full_solution = expand_planning_solution(room, full_solution, objective_reacher)
    solution = full_solution[: inspected_actions_index + 1]
    for action in solution:
        room = simulate_action(room, action)
    info = {
        "current_path": solution,
        "current_state": room,
        "found_solution": len(solution) == len(full_solution)
        and searcher.found_solution(),
    }
    return info
