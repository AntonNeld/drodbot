import asyncio
import numpy
import PIL
import tkinter
import traceback

from common import Strategy, Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room import Element

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
    event_loop
        The asyncio event loop for the backend thread.
    backend
        The backend containing the DRODbot.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._event_loop = event_loop
        self._backend = backend
        self._data = None
        self._selected_strategy = tkinter.StringVar(self)
        self._selected_strategy.set(list(Strategy)[0].value)

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
            self._state_controls, text="Save state", command=self._save_state
        )
        self._save_state_button.pack(side=tkinter.RIGHT)
        self._recheck_room_button = tkinter.Button(
            self._state_controls, text="Recheck room", command=self._recheck_room
        )
        self._recheck_room_button.pack(side=tkinter.RIGHT)

    def set_data(self, data):
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
            relative_x = x - self._data.current_room[0]
            relative_y = y - self._data.current_room[1]
            image_x = _CURRENT_ROOM_ORIGIN_X + relative_x * ROOM_WIDTH_IN_TILES
            image_y = _CURRENT_ROOM_ORIGIN_Y + relative_y * ROOM_HEIGHT_IN_TILES
            image[
                image_y : image_y + ROOM_HEIGHT_IN_TILES,
                image_x : image_x + ROOM_WIDTH_IN_TILES,
                :,
            ] = _room_to_image(room)
        # Draw plan
        if self._data.plan:
            plan_x = self._data.current_position[0] + _CURRENT_ROOM_ORIGIN_X
            plan_y = self._data.current_position[1] + _CURRENT_ROOM_ORIGIN_Y
            for action in self._data.plan:
                if action in [Action.N, Action.NE, Action.NW]:
                    plan_y -= 1
                if action in [Action.S, Action.SE, Action.SW]:
                    plan_y += 1
                if action in [Action.E, Action.SE, Action.NE]:
                    plan_x += 1
                if action in [Action.W, Action.SW, Action.NW]:
                    plan_x -= 1
                image[plan_y, plan_x, :] = [0, 0, 255]
        # Draw player position
        if self._data.current_position is not None:
            player_x = _CURRENT_ROOM_ORIGIN_X + self._data.current_position[0]
            player_y = _CURRENT_ROOM_ORIGIN_Y + self._data.current_position[1]
            image[
                player_y - 1 : player_y + 2,
                player_x - 1 : player_x + 2,
                :,
            ] = [255, 0, 0]
        pil_image = PIL.Image.fromarray(image)
        # Assign to self._view to prevent from being garbage collected
        self._view = PIL.ImageTk.PhotoImage(image=pil_image)
        self._canvas.create_image(0, 0, image=self._view, anchor=tkinter.NW)

    def _run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self._event_loop)

    def _run_strategy(self):
        strategy_value = self._selected_strategy.get()
        strategy = next(e for e in Strategy if e.value == strategy_value)
        self._run_coroutine(self._backend.run_strategy(strategy))

    def _save_state(self):
        self._run_coroutine(self._backend.save_state())

    def _recheck_room(self):
        self._run_coroutine(self._backend.recheck_room())


def _room_to_image(room):
    image = (
        numpy.ones((ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, 3), dtype=numpy.uint8)
        * 255
    )
    for (x, y) in room.find_coordinates(Element.WALL):
        image[y, x, :] = 0
    return image
