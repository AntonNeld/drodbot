import asyncio

import PIL
from PIL import ImageTk, Image, ImageDraw
import tkinter
import traceback

from common import TILE_SIZE, RoomSolverGoal
from room_simulator import Action
from .util import tile_to_text

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
_CANVAS_WIDTH = 418
_CANVAS_HEIGHT = 352
_LARGE_CANVAS_WIDTH = 836
_LARGE_CANVAS_HEIGHT = 704


class RoomSolverApp(tkinter.Frame):
    """This app is used to debug the room solver.

    It takes a room and tries to solve it step by step.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    backend
        The backend that contains the play interface.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._event_loop = event_loop
        self._backend = backend
        self._enlarged_view = False
        self._room_image = None
        self._room = None
        self._room_solver_info = None
        self._selected_goal = tkinter.StringVar(self)
        self._selected_goal.set(list(RoomSolverGoal)[0].value)
        self._heuristic_in_priority = tkinter.IntVar(self)
        self._heuristic_in_priority.set(1)
        self._path_cost_in_priority = tkinter.IntVar(self)
        self._path_cost_in_priority.set(1)
        self._avoid_duplicates = tkinter.IntVar(self)
        self._avoid_duplicates.set(1)
        self.focus_set()
        self.bind("<Right>", lambda x: self._expand_node())
        self.bind("<Left>", lambda x: self._rewind_expansion())

        # Create widgets
        self._canvas = tkinter.Canvas(
            self, width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, bg="white"
        )
        self._canvas.bind("<Button-1>", self._clicked_canvas)
        self._canvas.pack(side=tkinter.LEFT)
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.RIGHT)
        self._tile_content_text = tkinter.Label(self._control_panel, text="")
        self._tile_content_text.pack(side=tkinter.TOP)
        self._get_room_area = tkinter.Frame(self._control_panel)
        self._get_room_area.pack(side=tkinter.TOP)
        self._get_room_from_screenshot_button = tkinter.Button(
            self._get_room_area,
            text="Get room from screenshot",
            command=self._get_room_from_screenshot,
        )
        self._get_room_from_screenshot_button.pack(side=tkinter.LEFT)
        self._get_room_from_bot_button = tkinter.Button(
            self._get_room_area,
            text="Get room from bot",
            command=self._get_room_from_bot,
        )
        self._get_room_from_bot_button.pack(side=tkinter.LEFT)
        self._toggle_view_size_button = tkinter.Button(
            self._control_panel, text="Enlarge view", command=self._toggle_view_size
        )
        self._toggle_view_size_button.pack(side=tkinter.TOP)
        self._select_goal_dropdown = tkinter.OptionMenu(
            self._control_panel,
            self._selected_goal,
            *[o.value for o in RoomSolverGoal],
        )
        self._select_goal_dropdown.pack(side=tkinter.TOP)
        self._search_area = tkinter.Frame(self._control_panel)
        self._search_area.pack(side=tkinter.TOP)
        self._init_search_button = tkinter.Button(
            self._search_area, text="Init search", command=self._init_search
        )
        self._init_search_button.pack(side=tkinter.LEFT)
        self._rewind_button = tkinter.Button(
            self._search_area, text="<", command=self._rewind_expansion
        )
        self._rewind_button.pack(side=tkinter.LEFT)
        self._expand_node_button = tkinter.Button(
            self._search_area, text=">", command=self._expand_node
        )
        self._expand_node_button.pack(side=tkinter.LEFT)
        self._find_solution_button = tkinter.Button(
            self._search_area, text=">>", command=self._find_solution
        )
        self._find_solution_button.pack(side=tkinter.LEFT)
        self._checkboxes_1 = tkinter.Frame(self._control_panel)
        self._checkboxes_1.pack(side=tkinter.TOP)
        self._heuristic_checkbox = tkinter.Checkbutton(
            self._checkboxes_1,
            text="Heuristic in priority",
            variable=self._heuristic_in_priority,
        )
        self._heuristic_checkbox.pack(side=tkinter.LEFT)
        self._path_cost_checkbox = tkinter.Checkbutton(
            self._checkboxes_1,
            text="Path cost in priority",
            variable=self._path_cost_in_priority,
        )
        self._path_cost_checkbox.pack(side=tkinter.LEFT)
        self._checkboxes_2 = tkinter.Frame(self._control_panel)
        self._checkboxes_2.pack(side=tkinter.TOP)
        self._avoid_duplicates_checkbox = tkinter.Checkbutton(
            self._checkboxes_2, text="Avoid duplicates", variable=self._avoid_duplicates
        )
        self._avoid_duplicates_checkbox.pack(side=tkinter.LEFT)
        self._room_solver_text = tkinter.Label(self._control_panel, text="")
        self._room_solver_text.pack(side=tkinter.TOP)

    def set_data(self, room_image, room, room_solver_info):
        """Set the data to show in the app.

        Parameters
        ----------
        room_image
            Real image of the current room.
        room
            The simulated room.
        """
        if room_image is not None:
            self._room_image = room_image
        if room is not None:
            self._room = room
        if room_solver_info is not None:
            self._room_solver_info = room_solver_info
        self._draw_view()

    def _draw_view(self):
        if self._room_image is not None:
            pil_image = PIL.Image.fromarray(self._room_image)
            if self._room_solver_info is not None:
                if isinstance(self._room_solver_info["current_state"], tuple):
                    _draw_explored(pil_image, self._room_solver_info["explored_states"])
                    _draw_frontier(pil_image, self._room_solver_info["frontier_states"])
                    current_position = self._room_solver_info["current_state"]
                    _draw_position(
                        pil_image,
                        current_position,
                        self._room_solver_info["found_solution"],
                    )
                else:
                    current_position, _ = self._room_solver_info[
                        "current_state"
                    ].find_player()
                _draw_path(
                    pil_image,
                    current_position,
                    self._room_solver_info["current_path"],
                    self._room_solver_info["found_solution"],
                )

            resized_image = pil_image.resize(
                (int(self._canvas["width"]), int(self._canvas["height"])), Image.NEAREST
            )
            # Assign to self._view to prevent from being garbage collected
            self._view = ImageTk.PhotoImage(image=resized_image)
            self._canvas.create_image(0, 0, image=self._view, anchor=tkinter.NW)
        if self._room_solver_info is not None:
            self._room_solver_text.config(
                text=_solver_info_to_text(self._room_solver_info)
            )

    def _run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self._event_loop)

    def _get_room_from_screenshot(self):
        self._run_coroutine(self._backend.get_room_from_screenshot())

    def _get_room_from_bot(self):
        self._run_coroutine(self._backend.get_room_from_bot())

    def _init_search(self):
        goal_value = self._selected_goal.get()
        goal = next(e for e in RoomSolverGoal if e.value == goal_value)
        self._run_coroutine(
            self._backend.init_search(
                goal,
                self._heuristic_in_priority.get() == 1,
                self._path_cost_in_priority.get() == 1,
                self._avoid_duplicates.get() == 1,
            )
        )

    def _expand_node(self):
        self._run_coroutine(self._backend.expand_next_node())

    def _rewind_expansion(self):
        self._run_coroutine(self._backend.rewind_expansion())

    def _find_solution(self):
        self._run_coroutine(self._backend.find_solution())

    def _toggle_view_size(self):
        if self._enlarged_view:
            self._enlarged_view = False
            self._canvas.configure(height=_CANVAS_HEIGHT, width=_CANVAS_WIDTH)
            self._toggle_view_size_button.configure(text="Enlarge view")
            self._draw_view()
        else:
            self._enlarged_view = True
            self._canvas.configure(
                height=_LARGE_CANVAS_HEIGHT, width=_LARGE_CANVAS_WIDTH
            )
            self._toggle_view_size_button.configure(text="Ensmall view")
            self._draw_view()

    def _clicked_canvas(self, event):
        if self._enlarged_view:
            x = event.x // TILE_SIZE
            y = event.y // TILE_SIZE
        else:
            x = event.x // (TILE_SIZE // 2)
            y = event.y // (TILE_SIZE // 2)
        tile = self._room.get_tile((x, y))
        self._tile_content_text.config(text=tile_to_text(tile))


def _solver_info_to_text(room_solver_info):
    action_names = [e.name for e in room_solver_info["current_path"]]
    row_length = 20
    action_rows = [
        ",".join(action_names[i : i + row_length])
        for i in range(0, len(action_names), row_length)
    ]
    heuristic = room_solver_info["current_state_heuristic"]
    return "\n".join(
        [
            f"Iterations: {room_solver_info['iterations']}",
            f"Heuristic value of current state: {heuristic}",
            f"Frontier size {room_solver_info['frontier_size']}",
            f"Explored size {room_solver_info['explored_size']}",
            "Current path:",
            ",\n".join(action_rows),
        ]
    )


def _draw_position(pil_image, position, solved):
    x, y = position
    draw = ImageDraw.Draw(pil_image)
    draw.ellipse(
        [
            (x * TILE_SIZE, y * TILE_SIZE),
            ((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE),
        ],
        outline="green" if solved else "blue",
        width=3,
    )


def _draw_path(pil_image, end_position, actions, solved):
    # We'll draw the path backwards, since we know the end but not the start
    positions = [end_position]
    for action in reversed(actions):
        x, y = positions[-1]
        if action == Action.E:
            positions.append((x - 1, y))
        elif action == Action.SE:
            positions.append((x - 1, y - 1))
        elif action == Action.S:
            positions.append((x, y - 1))
        elif action == Action.SW:
            positions.append((x + 1, y - 1))
        elif action == Action.W:
            positions.append((x + 1, y))
        elif action == Action.NW:
            positions.append((x + 1, y + 1))
        elif action == Action.N:
            positions.append((x, y + 1))
        elif action == Action.NE:
            positions.append((x - 1, y + 1))
    draw = ImageDraw.Draw(pil_image)
    draw.line(
        [((p[0] + 0.5) * TILE_SIZE, (p[1] + 0.5) * TILE_SIZE) for p in positions],
        fill="green" if solved else "blue",
        width=3,
    )


def _draw_frontier(pil_image, frontier_states):
    for position in frontier_states:
        x, y = position
        draw = ImageDraw.Draw(pil_image)
        draw.ellipse(
            [
                ((x + 0.25) * TILE_SIZE, (y + 0.25) * TILE_SIZE),
                ((x + 0.75) * TILE_SIZE, (y + 0.75) * TILE_SIZE),
            ],
            outline="yellow",
            width=3,
        )


def _draw_explored(pil_image, explored_states):
    for position in explored_states:
        x, y = position
        draw = ImageDraw.Draw(pil_image)
        draw.ellipse(
            [
                ((x + 0.25) * TILE_SIZE, (y + 0.25) * TILE_SIZE),
                ((x + 0.75) * TILE_SIZE, (y + 0.75) * TILE_SIZE),
            ],
            outline="red",
            width=3,
        )
