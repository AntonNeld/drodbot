import numpy
import PIL
import tkinter
from queue import Empty

from apps.util import QUEUE_POLL_INTERVAL
from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from drod_bot.state.drod_bot_state import DrodBotState
from drod_bot import SaveTestRoomBehavior
from .backend import PlayingAppBackend, Strategy
from room_simulator import ElementType, Action, Room

_CANVAS_WIDTH = 190
_CANVAS_HEIGHT = 160
_CURRENT_ROOM_ORIGIN_X = 76
_CURRENT_ROOM_ORIGIN_Y = 64


class PlayingApp(tkinter.Frame):
    """This app is used to make DRODbot actually play DROD.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    backend
        The backend containing the DRODbot.
    """

    def __init__(self, root: tkinter.Frame, backend: PlayingAppBackend):
        super().__init__(root)
        self._main_window = root
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)
        self._backend = backend
        self._data = DrodBotState()
        self._selected_strategy = tkinter.StringVar(self)
        self._selected_strategy.set(list(Strategy)[0].value)
        self._save_test_rooms = tkinter.StringVar(self)
        self._save_test_rooms.set(SaveTestRoomBehavior.NO_SAVING.value)

        # Create widgets
        self._canvas = tkinter.Canvas(
            self, width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, bg="white"
        )
        self._canvas.pack(side=tkinter.LEFT)
        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.LEFT)
        self._run_controls = tkinter.Frame(self._control_panel)
        self._run_controls.pack(side=tkinter.TOP)
        self._strategy_dropdown = tkinter.OptionMenu(
            self._run_controls, self._selected_strategy, *[s.value for s in Strategy]
        )
        self._strategy_dropdown.pack(side=tkinter.LEFT)
        self._go = tkinter.Button(
            self._run_controls, text="Go", command=self._run_strategy
        )
        self._go.pack(side=tkinter.RIGHT)
        self._state_controls = tkinter.Frame(self._control_panel)
        self._state_controls.pack(side=tkinter.TOP)
        self._save_state_button = tkinter.Button(
            self._state_controls, text="Save state", command=self._backend.save_state
        )
        self._save_state_button.pack(side=tkinter.RIGHT)
        self._clear_state_button = tkinter.Button(
            self._state_controls, text="Clear state", command=self._backend.clear_state
        )
        self._clear_state_button.pack(side=tkinter.RIGHT)
        self._recheck_room_button = tkinter.Button(
            self._state_controls,
            text="Recheck room",
            command=self._backend.recheck_room,
        )
        self._recheck_room_button.pack(side=tkinter.RIGHT)
        self._save_room_controls = tkinter.Frame(self._control_panel)
        self._save_room_controls.pack(side=tkinter.TOP)
        self._save_test_rooms_dropdown = tkinter.OptionMenu(
            self._save_room_controls,
            self._save_test_rooms,
            *[s.value for s in SaveTestRoomBehavior]
        )
        self._save_test_rooms_dropdown.pack(side=tkinter.LEFT)

    def _check_queue(self):
        """Check the queue for updates."""
        try:
            data = self._backend.get_queue().get(block=False)
            self.set_data(data)
        except Empty:
            pass
        self._main_window.after(QUEUE_POLL_INTERVAL, self._check_queue)

    def set_data(self, data: DrodBotState):
        """Set the DRODbot state to show in the app.

        Parameters
        ----------
        data
            The DRODbot state.
        """
        self._data = data
        self._draw_level()

    def _draw_level(self):
        image = numpy.ones((_CANVAS_HEIGHT, _CANVAS_WIDTH, 3), dtype=numpy.uint8) * 128
        # Draw rooms
        for (x, y), room in self._data.level.rooms.items():
            relative_x = x - self._data.current_room_position[0]
            relative_y = y - self._data.current_room_position[1]
            if (
                relative_x > -3
                and relative_x < 3
                and relative_y > -3
                and relative_y < 3
            ):
                image_x = _CURRENT_ROOM_ORIGIN_X + relative_x * ROOM_WIDTH_IN_TILES
                image_y = _CURRENT_ROOM_ORIGIN_Y + relative_y * ROOM_HEIGHT_IN_TILES
                image[
                    image_y : image_y + ROOM_HEIGHT_IN_TILES,
                    image_x : image_x + ROOM_WIDTH_IN_TILES,
                    :,
                ] = _room_to_image(room)
        if self._data.current_room is not None:
            (player_x, player_y), _ = self._data.current_room.find_player()
            # Draw plan
            if self._data.plan:
                plan_x = player_x + _CURRENT_ROOM_ORIGIN_X
                plan_y = player_y + _CURRENT_ROOM_ORIGIN_Y
                for action in self._data.plan:
                    if action in [Action.N, Action.NE, Action.NW]:
                        plan_y -= 1
                    if action in [Action.S, Action.SE, Action.SW]:
                        plan_y += 1
                    if action in [Action.E, Action.SE, Action.NE]:
                        plan_x += 1
                    if action in [Action.W, Action.SW, Action.NW]:
                        plan_x -= 1
                    if (
                        plan_x >= 0
                        and plan_x < _CANVAS_WIDTH
                        and plan_y >= 0
                        and plan_y < _CANVAS_HEIGHT
                    ):
                        image[plan_y, plan_x, :] = [0, 0, 255]
            # Draw player position
            image_player_x = _CURRENT_ROOM_ORIGIN_X + player_x
            image_player_y = _CURRENT_ROOM_ORIGIN_Y + player_y
            image[
                image_player_y - 1 : image_player_y + 2,
                image_player_x - 1 : image_player_x + 2,
                :,
            ] = [255, 0, 0]
        pil_image = PIL.Image.fromarray(image)
        # Assign to self._view to prevent from being garbage collected
        self._view = PIL.ImageTk.PhotoImage(image=pil_image)
        self._canvas.create_image(0, 0, image=self._view, anchor=tkinter.NW)

    def _run_strategy(self):
        strategy = next(e for e in Strategy if e.value == self._selected_strategy.get())
        save_test_rooms = next(
            e for e in SaveTestRoomBehavior if e.value == self._save_test_rooms.get()
        )
        self._backend.run_strategy(strategy, save_test_rooms=save_test_rooms)


def _room_to_image(room: Room):
    image = (
        numpy.ones((ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, 3), dtype=numpy.uint8)
        * 255
    )
    for (x, y) in room.find_coordinates(ElementType.WALL):
        image[y, x, :] = 0
    return image
